# 🚀 Kubernetes End-to-End Deployment (EKS + RDS + Ingress)

This project demonstrates a **complete end-to-end Kubernetes deployment on AWS EKS**, including:

* Frontend + Backend deployment
* AWS RDS (MySQL) integration
* NGINX Ingress Controller
* Domain & HTTPS setup
* IRSA (IAM Roles for Service Accounts)

---

## 🧠 Architecture Overview

```text
User → DNS → AWS ELB → NGINX Ingress → Frontend → Backend → RDS
```

As per project flow:

* DNS routes traffic to AWS Load Balancer
* Ingress routes traffic to services
* Backend connects securely to RDS

---

## 🛠️ Tech Stack

* Kubernetes (EKS)
* AWS (EC2, EKS, RDS, ECR, ACM)
* Docker
* Helm
* NGINX Ingress Controller
* MySQL (RDS)

---

## 📦 Project Features

* 🔹 EKS cluster setup
* 🔹 Docker image build & push to ECR
* 🔹 Secure DB connection using IRSA
* 🔹 Domain-based routing with Ingress
* 🔹 HTTPS using ACM certificate
* 🔹 Multi-namespace architecture

---

## 📁 Project Structure

```bash
deployment/
  frontend/
  backend/

networking/
  ingress.yaml
  nginx-ingress-controller.yaml
```

---

## ⚙️ Prerequisites

Install:

```bash
aws cli
kubectl
eksctl
docker
git
```

---

## 🔥 Setup Steps

---

### 🔹 Step 1: Create EKS Cluster

```bash
eksctl create cluster \
 --name datastore-cluster \
 --region us-east-1 \
 --nodegroup-name workers \
 --node-type t3.medium \
 --nodes 2 \
 --managed
```

---

### 🔹 Step 2: Configure kubectl

```bash
aws eks update-kubeconfig --name datastore-cluster --region us-east-1
kubectl get nodes
```

---

### 🔹 Step 3: Create RDS MySQL

* Engine: MySQL 8.0
* Public access: ❌ Disabled
* Enable IAM authentication

👉 Copy RDS endpoint

---

### 🔹 Step 4: Create ECR Repositories

* datastore-frontend
* datastore-backend

---

### 🔹 Step 5: Build & Push Docker Images

```bash
docker build -t datastore-backend .
docker tag datastore-backend:latest <ECR_URI>
docker push <ECR_URI>
```

---

### 🔹 Step 6: Configure IRSA

* Create IAM policy
* Create IAM role
* Attach role to ServiceAccount

---

### 🔹 Step 7: Deploy Kubernetes Resources

#### Namespaces

```bash
kubectl apply -f deployment/frontend/namespace.yaml
kubectl apply -f deployment/backend/namespace.yaml
```

#### Backend

```bash
kubectl apply -f deployment/backend/backend-sa.yaml
kubectl apply -f deployment/backend/datastore-be-cm.yaml
kubectl apply -f deployment/backend/datastore-be-secret.yaml
kubectl apply -f deployment/backend/datastore-be.yaml
```

#### Frontend

```bash
kubectl apply -f deployment/frontend/datastore-fe-cm.yaml
kubectl apply -f deployment/frontend/datastore-fe.yaml
```

---

### 🔹 Step 8: Install NGINX Ingress Controller

```bash
kubectl apply -f networking/nginx-ingress-controller.yaml
kubectl get pods -n ingress-nginx
```

---

### 🔹 Step 9: Configure Ingress

```bash
kubectl apply -f networking/ingress.yaml
kubectl get ingress -n frontend
```

---

### 🔹 Step 10: Configure DNS (GoDaddy)

* Add CNAME:

  * Name: `datastore`
  * Value: ELB DNS

---

## 🌐 Final Access

```text
https://datastore.yourdomain.com
```

---

## 🔍 Key Concepts Used

* **Namespace** → Isolation of resources
* **Deployment** → Manage pods & replicas
* **Service (ClusterIP)** → Internal communication
* **ConfigMap & Secret** → Configuration & sensitive data
* **Ingress** → External traffic routing
* **IRSA** → Secure AWS access without credentials

---

## 🧪 Debug Commands

```bash
kubectl get pods --all-namespaces
kubectl get svc --all-namespaces
kubectl get ingress -n frontend
kubectl logs <pod-name>
kubectl describe pod <pod-name>
```

---

## ⚠️ Common Issues

| Issue                 | Fix                   |
| --------------------- | --------------------- |
| Image pull error      | Push image to ECR     |
| Ingress not working   | Check ELB & DNS       |
| RDS connection failed | Verify security group |
| Pod crash             | Check logs            |

---

## 🧹 Cleanup

```bash
kubectl delete namespace frontend
kubectl delete namespace backend
kubectl delete namespace ingress-nginx
```

---

## 🎯 Conclusion

This project demonstrates:

* Real-world Kubernetes deployment
* Cloud-native architecture
* Secure and scalable design

---

## 👨‍💻 Author

**Bijaya Patra**

---

## ⭐ Give a Star if you like this project!
