---
sidebar_label: Faster Model Loading
tags: 
- deployment
- kubernetes
- loading
---

# Faster Model Loading

LLM weights need to be loaded from the internet during the initial startup of inference containers. These downloads can significantly delay your first deployments, scaling operations, and downtime during upgrades. This is especially problematic when running GPU workloads, where provisioning additional high-performance nodes for blue-green deployments is very expensive.

This guide covers two main approaches to accelerate model loading: **InitContainers** (recommended) and **Persistent Volumes**. InitContainers leverage Kubernetes node caching to eliminate startup download delays, while persistent volumes offer an alternative approach with notable trade-offs.

## InitContainers (Recommended)

InitContainers leverage Kubernetes distributed node caching to preload model weights wrapped in lightweight containers. By mounting the model directory from the init container into the runtime inference container, we eliminate the need to download weights at startup.

This approach offers several advantages:

- **Fast restarts**: Once pulled on a node, every restart or new runtime on that node skips model downloads
- **Efficient storage**: Models are cached at the node level, avoiding duplication across replicas
- **Simplified orchestration**: No complex volume management or access coordination required

The solution consists of two components: **Bit Harbor** (pre-built model containers) and **Pre-Porter** (automated distribution across nodes).

### Bit Harbor <a href="https://github.com/doublewordai/bit-harbor" target="_blank" style={{textDecoration: 'none', marginLeft: '8px'}}><svg style={{width: '22px', height: '22px', verticalAlign: 'middle'}} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.30 3.297-1.30.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg></a>

Bit Harbor provides pre-built containers with popular model weights. You can configure any inference runtime to use these containers by specifying the init container in your Inference Stack Helm chart values:

```yaml
modelGroups:
  vllm-example:
    # Init container to copy model weights from bit-harbor
    initContainers:
      - name: copy-model-weights
        image: ghcr.io/doublewordai/bit-harbor:gemma-3-12b-it
        command: ["/pause"]
        volumeMounts:
          - name: models
            mountPath: /models
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi

    # Volume mounts for main container
    volumeMounts:
      - name: models
        mountPath: /root/.cache/huggingface
        readOnly: false

    # Shared volume for model weights (emptyDir for fast access)
    volumes:
      - name: models
        emptyDir:
          sizeLimit: 50Gi  # Adjust based on model size
```

### Pre-Porter <a href="https://github.com/doublewordai/bit-harbor/preporter" target="_blank" style={{textDecoration: 'none', marginLeft: '8px'}}><svg style={{width: '22px', height: '22px', verticalAlign: 'middle'}} viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.30 3.297-1.30.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg></a>

While Bit Harbor provides the model containers, Pre-Porter ensures they're distributed across your cluster nodes before they're needed. This eliminates the initial download delay that occurs when a node encounters a model for the first time.

Pre-Porter runs as a scheduled job that periodically pulls model containers to all worker nodes, ensuring immediate availability when inference pods are deployed.

#### Installation

Install Pre-Porter using Helm:

```bash
helm install pre-porter oci://ghcr.io/doublewordai/bit-harbor/pre-porter --values values.yaml
```

Configure it with the following values:

```yaml
# All model weights you want kept cached on your nodes, to see the full available list: https://github.com/doublewordai/bit-harbor/blob/main/models.json
images:
  - name: "gemma-3-12b-it"
    pullPolicy: "Always"
    enabled: true

advancedCronJob:
  enabled: true
  schedule: "0 * * * *"  # Every hour

  broadcastJobTemplate:
    ttlSecondsAfterFinished: 3600  # 1 hour
```

#### Targeting Specific Nodes

To conserve storage space, you can configure Pre-Porter to only cache models on specific nodes using node selectors and tolerations. For example, to target only nodes with GPUs:

```yaml
# Only schedule on nodes with GPU
globalNodeSelector:
  nvidia.com/gpu.present: "true"

globalTolerations:
  - key: nvidia.com/gpu
    value: present
    effect: NoSchedule
```

## Persistent Volumes

Another alternative is to use persistent volumes with replica sets to save repeated downloads by using a permanently mounted directory for your huggingface cache. However, this approach comes with significant trade-offs that make it less ideal than init containers.

### Volume Access Patterns

You have two main options for persistent volume access, each with distinct challenges:

#### Single Access Volumes (ReadWriteOnce)

- Requires provisioning a separate volume per replica
- Creates deployment complexity during upgrades, as the current pod must release its claim before a new pod can acquire the volume
- Makes pod migration between nodes difficult

#### Shared Access Volumes (ReadWriteMany)

- Introduces concurrency risks since inference runtimes typically require write access to model directories
- Can lead to race conditions or data corruption when multiple pods write simultaneously
- Requires careful coordination between replicas

### Storage Inefficiency

Regardless of the access pattern chosen, persistent volumes suffer from storage duplication issues. When multiple replicas run on the same node, each stores its own copy of the model weights, leading to unnecessary storage overhead.

For these reasons, persistent volumes are not our preferred method for model weight management.
