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

### [Bit Harbor](https://github.com/doublewordai/bit-harbor)

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

### [Pre-Porter](https://github.com/doublewordai/bit-harbor/preporter)

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
