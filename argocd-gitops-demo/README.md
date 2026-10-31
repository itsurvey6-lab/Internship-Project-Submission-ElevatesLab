
# Argo CD GitOps Demo

## Objective
Deploy and manage a Kubernetes application using GitOps with Argo CD.

## Technology Stack
- Kubernetes (K3s)
- Argo CD
- Git and GitHub
- NGINX

## Kubernetes Resources
- Namespace: gitops-demo
- Deployment: gitops-demo
- Service: gitops-demo

## GitOps Workflow
1. Store Kubernetes manifests in GitHub.
2. Configure Argo CD to monitor the repository.
3. Synchronize repository changes to Kubernetes.
4. Commit changes to Git and observe the deployed state.
