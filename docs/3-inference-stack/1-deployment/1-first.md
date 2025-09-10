---
sidebar_label: First Deployment
tags: 
- deployment
- kubernetes
- helm
---

# Kubernetes Deployment Guide

This guide provides instructions for deploying the Doubleword Inference Stack to Kubernetes using Helm.

Kubernetes deployment is ideal for organizations requiring high availability, automatic scaling, and integration with existing Kubernetes infrastructure. For simpler single-server deployments, we recommend running containers directly.

## Prerequisites

Before beginning your deployment, ensure you have the necessary infrastructure and credentials prepared.

### System Requirements

Your Kubernetes cluster must be running version 1.24 or later with kubectl
configured to access your target cluster. You'll also need Helm 3.8 or later
installed for managing the deployment.

### Node Availability

Ensure that your Kubernetes nodes have sufficient resources (CPU, memory, and disk space) to run the Inference Stack components. It's recommended to use dedicated nodes for production deployments.

## Installing the Helm Chart

The Inference Stack Helm chart is distributed through GitHub Container Registry
as an OCI artifact. First, create a dedicated namespace for your deployment:

```bash
kubectl create namespace inference-stack
```

Install the chart directly from the OCI registry (this will require you to
authenticate. Contact your account manager if you don't have access):

```bash
helm install inference-stack oci://ghcr.io/doublewordai/inference-stack \
  --namespace inference-stack \
  --values values.yaml
```

## Configuration with Values

Create a `values.yaml` file to customize your deployment. This file contains
the essential configuration for your Control Layer installation.

### Model Groups

Models are added under the `modelGroups` key in the `values.yaml` file. You can transparently run any inference container and they will be managed by the Inference Stack.

* `image`: Container image configuration
* `modelAlias`: A list of strings that will be used to route requests to this model.
* `modelName`: The name of the model the container expects to receive.
* `command`: The command to run the model server.

```yaml
modelGroups:
  # vLLM deployment serving Llama models
  vllm-llama:
    enabled: true

    image:
      repository: vllm/vllm-openai
      tag: latest
      pullPolicy: Always

    modelAlias:
      - "llama"
      - "llama-3.1-8b-instruct"
    modelName: "meta-llama/Meta-Llama-3.1-8B-Instruct"

    command:
      - "vllm"
      - "serve"
      - "--model"
      - "meta-llama/Meta-Llama-3.1-8B-Instruct"
    
  # SGLang deployment serving Qwen models  
  sglang-qwen:
    enabled: true
    image:
      repository: lmsysorg/sglang
      tag: latest
      pullPolicy: Always

    modelAlias:
      - "qwen"
      - "qwen-2.5-7b-instruct"
    modelName: "Qwen/Qwen2.5-7B-Instruct"
    
    command:
      - "python"
      - "-m"
      - "sglang.launch_server"
      - "--model-path"
      - "Qwen/Qwen2.5-7B-Instruct"
```

### GPU Configuration

For GPU-enabled inference you can assign these resources to your models:

```yaml
modelGroups:
  vllm-llama:
    resources:
      limits:
        nvidia.com/gpu: 2
        memory: 16Gi
      requests:
        nvidia.com/gpu: 2
        memory: 8Gi

    nodeSelector:
      accelerator: nvidia-h100

    tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
```

### Deployment Strategy Configuration

```yaml
modelGroups:
  vllm-llama:
    # Rolling update strategy for zero-downtime deployments
    strategy:
      type: RollingUpdate
      rollingUpdate:
        maxSurge: 1          # Allow 1 extra pod during updates
        maxUnavailable: 0    # Never take pods down (blue-green)
    
    # Scale replicas for high availability
    replicaCount: 3
```
