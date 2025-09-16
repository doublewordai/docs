---
sidebar_label: Getting Started
tags: 
- deployment
- kubernetes
- helm
---

# Your First Deployment

In this guide, we'll walk you through the steps to deploy the Doubleword Inference Stack using Helm on a Kubernetes cluster. Customization and advanced configurations will not be covered in this introductory guide.

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
  vllm-example:
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
  vllm-example:
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

### Shared Memory

If you are running models in tensor parallel you will need to increase the default shared memory size. You can do this by adding an `emptyDir` volume for shared memory:

```yaml
modelGroups:
  vllm-example:
    volumeMounts:
      - name: shm
        mountPath: /dev/shm

    volumes:
      - name: shm
        emptyDir:
          medium: Memory
          sizeLimit: 20Gi
```

### Gated Model Weights

:::note
If you are using [bit harbor](./2-loading.md#bit-harbor) initContainers to speed up model downloads this is not necessary.
:::

Some model providers gate access to their models using API keys and you need to supply these to your inference container so they can download the weights. You can do this by creating a Kubernetes secret and referencing it in your `values.yaml` file.

```yaml
modelGroups:
  vllm-example:
    env:
      - name: HF_TOKEN
        valueFrom:
          secretKeyRef:
            name: hf-secret
            key: HUGGING_FACE_HUB_TOKEN
```

Which pulls your Hugging Face access token from a kubernetes secret which can be created using:

```bash
kubectl create secret generic hf-secret --from-literal=HUGGING_FACE_HUB_TOKEN=<your_token>
```
