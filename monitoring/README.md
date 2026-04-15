# 📊 Kubernetes Monitoring Setup (Prometheus + Grafana)

This project demonstrates how to implement **monitoring in Kubernetes (EKS)** using **Prometheus and Grafana**.

---

## 🚀 Overview

Monitoring helps track:

* Application performance
* CPU & Memory usage
* Pod health
* Request metrics

### 🧠 Architecture

```
Application → Service → Prometheus → Grafana
```

* **Prometheus**: Collects metrics from application
* **Grafana**: Visualizes metrics in dashboards

---

## 🛠️ Tech Stack

* Kubernetes (EKS)
* Prometheus
* Grafana
* Helm
* AWS EBS (for storage)

---

## 📁 Files Used

* `storage.yaml` → StorageClass for EBS
* `monitoring.yaml` → App service + deployment with Prometheus annotations

---

## ⚙️ Prerequisites

Make sure you have:

```bash
kubectl
helm
aws cli
eksctl
```

---

## 🔥 Step-by-Step Setup

---

### 🔹 Step 1: Apply StorageClass

```bash
kubectl apply -f storage.yaml
kubectl get storageclass
```

---

### 🔹 Step 2: Install EBS CSI Driver

```bash
helm repo add aws-ebs-csi-driver https://kubernetes-sigs.github.io/aws-ebs-csi-driver
helm repo update

helm upgrade --install aws-ebs-csi-driver \
aws-ebs-csi-driver/aws-ebs-csi-driver \
--namespace kube-system
```

---

### 🔹 Step 3: Install Prometheus

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

kubectl create namespace prometheus

helm install prometheus prometheus-community/prometheus \
--namespace prometheus \
--set server.persistentVolume.storageClass="monitor-ebs-storage" \
--set alertmanager.persistence.enabled=true \
--set alertmanager.persistence.storageClass=monitor-ebs-storage
```

---

### 🔹 Step 4: Expose Prometheus

```bash
kubectl expose service prometheus-server \
--type=LoadBalancer \
--target-port=9090 \
--name=prometheus-lb -n prometheus

kubectl get svc -n prometheus
```

---

### 🔹 Step 5: Deploy Application (Monitoring Enabled)

```bash
kubectl apply -f monitoring.yaml
```

### ✅ Important Annotations

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/path: /actuator/prometheus
  prometheus.io/port: "8081"
```

---

### 🔹 Step 6: Verify in Prometheus

* Open Prometheus UI
* Go to: **Status → Targets**

✅ Expected:

```
mysv-cip → UP
```

---

### 🔹 Step 7: Install Grafana

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

kubectl create namespace grafana

helm install grafana grafana/grafana \
--namespace grafana \
--set persistence.storageClassName="monitor-ebs-storage" \
--set persistence.enabled=true \
--set adminPassword='shiva' \
--set service.type=LoadBalancer
```

---

### 🔹 Step 8: Access Grafana

```bash
kubectl get svc -n grafana
```

* Open EXTERNAL-IP in browser
* Login:

  * Username: `admin`
  * Password: `shiva`

---

### 🔹 Step 9: Add Prometheus Data Source

URL:

```
http://prometheus-server.prometheus.svc.cluster.local
```

Click **Save & Test**

---

### 🔹 Step 10: Import Dashboard

* Go to Dashboards → Import
* Use ID: `6417`

---

## 📊 Metrics Endpoint

Application exposes metrics at:

```
/actuator/prometheus
```

---

## 🧪 Troubleshooting

### ❌ Target DOWN / UNKNOWN

* Check service annotations
* Verify endpoint:

```bash
kubectl get endpoints mysv-cip
```

* Check pod logs:

```bash
kubectl logs <pod-name>
```

---

### ❌ No Data in Grafana

* Verify Prometheus datasource
* Check Prometheus targets
* Adjust time range

---

## ⚠️ Cost Note

⚠️ AWS resources incur cost. Delete after use:

```bash
helm uninstall grafana -n grafana
helm uninstall prometheus -n prometheus
```

---

## 🎯 Conclusion

This setup enables:

* Real-time monitoring
* Application observability
* Scalable DevOps practices

---

## 📌 Author

**Bijaya Patra**

---

## ⭐ If you found this useful, give it a star!
