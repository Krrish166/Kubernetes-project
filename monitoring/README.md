# Kubernetes Monitoring — Prometheus + Grafana

**Yeh document ek complete guide hai** — Kubernetes cluster pe Prometheus aur Grafana se monitoring setup karne ka poora process, shuru se end tak. Agar aage kabhi yeh karna pade, toh sirf yeh document follow karo.

---

## Table of Contents

1. [Monitoring kya hota hai aur kyun zaroori hai](#1-monitoring-kya-hota-hai)
2. [Architecture — Poora System Kaise Kaam Karta Hai](#2-architecture)
3. [Components aur Unka Kaam](#3-components-aur-unka-kaam)
4. [Prerequisites — Shuru Karne Se Pehle](#4-prerequisites)
5. [Phase 1 — AWS EKS Cluster Setup](#5-phase-1--aws-eks-cluster-setup)
6. [Phase 2 — EBS Storage Driver](#6-phase-2--ebs-storage-driver)
7. [Phase 3 — Prometheus Install](#7-phase-3--prometheus-install)
8. [Phase 4 — Application Deploy](#8-phase-4--application-deploy)
9. [Phase 5 — Grafana Install](#9-phase-5--grafana-install)
10. [Phase 6 — Grafana Configure + Dashboard](#10-phase-6--grafana-configure--dashboard)
11. [Custom Dashboard Banana](#11-custom-dashboard-banana)
12. [Auto-Switch Playlist](#12-auto-switch-playlist)
13. [Important Queries — PromQL](#13-important-queries--promql)
14. [Troubleshooting](#14-troubleshooting)
15. [Files Reference](#15-files-reference)
16. [Cost Warning](#16-cost-warning)

---

## 1. Monitoring kya hota hai

**Simple bhasha mein:** Tumhara application chal raha hai — lekin kaise pata chalega ki server ka CPU full ho gaya, memory khatam ho rahi hai, ya koi pod crash hua? Yahi kaam monitoring karta hai.

```
Bina monitoring ke:        Monitoring ke saath:
━━━━━━━━━━━━━━━━━━        ━━━━━━━━━━━━━━━━━━━━━
"Kuch toot gaya!"    →    "Pod X 5 minute pehle crash hua,
"Pata nahi kyun..."        CPU 95% tha, memory 2GB use ho rahi thi"
"User complaint aaya"      Alert already aa chuka tha
```

**Prometheus** data collect karta hai. **Grafana** use sundar charts mein dikhata hai.

---

## 2. Architecture

### Poora System Ek Nazar Mein

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS EKS CLUSTER                          │
│                                                                 │
│   ┌─────────────┐    ┌────────────────────────────────────┐    │
│   │ Data Sources│    │           PROMETHEUS               │    │
│   │             │    │  ┌──────────┐  ┌──────┐  ┌──────┐ │    │
│   │ • K8S Nodes │───▶│  │ Retrieval│─▶│ TSDB │  │ HTTP │ │    │
│   │ • Pods      │    │  │(scraping)│  │(store│  │Server│ │    │
│   │ • Datastore │    │  └──────────┘  └──────┘  └──────┘ │    │
│   │   App       │    │                   │                 │    │
│   └─────────────┘    │  ┌─────────────┐  │                │    │
│                      │  │Alert Manager│  ▼                │    │
│   ┌─────────────┐    │  │(conditions) │ EBS Volume        │    │
│   │ Push Gateway│───▶│  └──────┬──────┘ (AWS Disk)        │    │
│   │(short jobs) │    └─────────│──────────────────────────┘    │
│   └─────────────┘              │                               │
│                                │                               │
│                                ▼                               │
│                    ┌───────────────────┐                       │
│                    │   Alert Manager   │──▶ Slack / Email /    │
│                    └───────────────────┘    MS Teams           │
│                                                                 │
│   ┌─────────────────────────────────────────────────────┐      │
│   │                    GRAFANA                          │      │
│   │  Prometheus se data leta hai → Charts banata hai   │      │
│   │  Aap browser mein yahan dekhte ho                  │      │
│   └─────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### Data ka Safar — Step by Step

```
Application/Node
      │
      │  (metrics expose karta hai)
      ▼
http://pod-ip:port/actuator/prometheus   ← endpoint
      │
      │  (Prometheus har 15 sec mein yahan aata hai — "scraping")
      ▼
Prometheus TSDB (Time Series Database)
      │
      │  (Grafana query karta hai)
      ▼
Grafana Dashboard ← aap yahan dekhte ho (browser mein)
```

---

## 3. Components aur Unka Kaam

### Priority Order (Sabse Zaroori Pehle)

---

### ⭐⭐⭐ Prometheus — Sabse Important

| Cheez | Detail |
|-------|--------|
| **Kya hai** | Metrics collector + time-series database |
| **Kaam** | Applications aur nodes se data scrape karta hai, store karta hai |
| **Port** | 9090 |
| **Namespace** | `prometheus` |
| **Data store** | AWS EBS volume pe (restart hone pe data bachta hai) |
| **Scraping interval** | Har 15 seconds mein data lena |

**Prometheus ke andar kya kya hai:**

```
prometheus/
├── prometheus-server        ← main engine (scraping + storage)
├── prometheus-alertmanager  ← alert bhejta hai
├── prometheus-node-exporter ← node ka CPU/RAM/Disk data expose karta hai
├── kube-state-metrics       ← K8s resources ka data (pods, deployments)
└── prometheus-pushgateway   ← short-lived jobs ka data receive karta hai
```

**Prometheus scraping kaise karta hai — Annotation magic:**

Kisi bhi application ko monitor karna ho, sirf yeh 2 annotations daalo Service YAML mein:

```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"      # ← yeh batata hai "mujhe scrape karo"
    prometheus.io/path: /actuator/prometheus  # ← yeh batata hai "kahan se lena hai data"
```

Bas! Prometheus automatically detect kar lega.

---

### ⭐⭐⭐ Grafana — Visualization

| Cheez | Detail |
|-------|--------|
| **Kya hai** | Dashboard aur visualization tool |
| **Kaam** | Prometheus se data lekar sundar charts banata hai |
| **Port** | 3000 (LoadBalancer se browser mein khulta hai) |
| **Namespace** | `grafana` |
| **Default Login** | admin / shiva |
| **Data source** | Prometheus se connect hota hai |

---

### ⭐⭐ AWS EBS CSI Driver — Storage

| Cheez | Detail |
|-------|--------|
| **Kya hai** | AWS ka disk driver Kubernetes ke liye |
| **Kaam** | Prometheus ka data AWS EBS disk pe store karta hai |
| **Namespace** | `kube-system` |
| **StorageClass** | `monitor-ebs-storage` |
| **Zaroori kyun** | Bina iske pod restart hone pe Prometheus ka sara data delete ho jaata |

---

### ⭐⭐ kube-state-metrics

| Cheez | Detail |
|-------|--------|
| **Kya hai** | Kubernetes resources ka status metrics mein export karta hai |
| **Kaam** | Pods, Deployments, Nodes ka state Prometheus ko deta hai |
| **Example metrics** | `kube_pod_status_phase`, `kube_deployment_replicas` |

---

### ⭐ Node Exporter

| Cheez | Detail |
|-------|--------|
| **Kya hai** | Har node pe chalne wala agent |
| **Kaam** | Server ka CPU, RAM, Disk, Network metrics expose karta hai |
| **Example metrics** | `node_cpu_seconds_total`, `node_memory_MemAvailable_bytes` |

---

### ⭐ Push Gateway

| Cheez | Detail |
|-------|--------|
| **Kya hai** | Short-lived jobs ke liye buffer |
| **Kaam** | Jobs jo jaldi khatam ho jaate hain woh apna data yahan push karte hain |
| **Zaroori kyun** | Prometheus pull-based hai — agar job khatam ho gayi toh scrape nahi kar sakta |

---

### PromQL — Query Language

Grafana mein data dekhne ke liye yeh language use hoti hai:

```
sum(kube_pod_status_phase{phase="Running"})
      ↑          ↑                ↑
  function    metric name      filter
```

---

## 4. Prerequisites

Yeh sab pehle install hona chahiye:

```bash
# 1. AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install
aws configure
# Maangega: Access Key ID, Secret Access Key, Region (us-east-1), Output format (json)

# 2. kubectl
curl -LO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# 3. eksctl
curl --silent --location "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# 4. Helm (Kubernetes ka app install tool)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify sab install hua
aws --version && kubectl version --client && eksctl version && helm version
```

**AWS IAM Setup:**
- AWS Console → IAM → Users → Apna user → Add permissions
- `AdministratorAccess` policy attach karo (practice ke liye)

---

## 5. Phase 1 — AWS EKS Cluster Setup

> EKS = Elastic Kubernetes Service. AWS ka managed Kubernetes — tumhe manually cluster maintain nahi karna padta.

```bash
# Cluster banao (10-15 minute lagega, wait karo)
eksctl create cluster \
  --name my-monitoring-cluster \
  --region us-east-1 \
  --nodegroup-name workers \
  --node-type t3.medium \
  --nodes 1 \
  --managed

# kubectl ko cluster se connect karo
aws eks update-kubeconfig --region us-east-1 --name my-monitoring-cluster

# Verify — "Ready" status aana chahiye
kubectl get nodes
```

**Expected output:**
```
NAME                          STATUS   ROLES    AGE   VERSION
ip-192-168-7-44.ec2.internal  Ready    <none>   2m    v1.28.x
```

---

## 6. Phase 2 — EBS Storage Driver

> Prometheus ka data AWS disk pe save karne ke liye yeh driver zaroori hai.

**Step 1: IAM Policy attach karo**
```
AWS Console → EKS → Clusters → my-monitoring-cluster
→ Compute → Node groups → workers
→ Node IAM role pe click karo
→ Add permissions → Attach policies
→ "AmazonEBSCSIDriverPolicy" search karo → Add
```

**Step 2: Driver install karo**
```bash
# Repo add karo
helm repo add aws-ebs-csi-driver https://kubernetes-sigs.github.io/aws-ebs-csi-driver
helm repo update

# Install karo
helm upgrade --install aws-ebs-csi-driver \
  aws-ebs-csi-driver/aws-ebs-csi-driver \
  --namespace kube-system

# Verify
kubectl get pods -n kube-system | grep ebs
# ebs-csi-controller-xxx   Running hona chahiye
```

**Step 3: StorageClass apply karo**

`storage.yml` file ka content:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: monitor-ebs-storage
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
parameters:
  type: gp2
```

```bash
kubectl apply -f storage.yml

# Verify
kubectl get storageclass
# monitor-ebs-storage dikhna chahiye
```

---

## 7. Phase 3 — Prometheus Install

```bash
# Helm repo add karo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Namespace banao
kubectl create namespace prometheus

# Prometheus install karo with EBS storage
helm install prometheus prometheus-community/prometheus \
  --namespace prometheus \
  --set server.persistentVolume.storageClass="monitor-ebs-storage" \
  --set alertmanager.persistence.enabled=true \
  --set alertmanager.persistence.storageClass=monitor-ebs-storage

# Pods check karo (2-3 min wait karo)
kubectl get pods -n prometheus
```

**Expected pods:**
```
NAME                                        READY   STATUS
prometheus-server-xxx                       2/2     Running
prometheus-alertmanager-xxx                 1/1     Running
prometheus-kube-state-metrics-xxx           1/1     Running
prometheus-prometheus-node-exporter-xxx     1/1     Running
prometheus-prometheus-pushgateway-xxx       1/1     Running
```

**Prometheus ko browser mein access karo:**
```bash
# LoadBalancer se expose karo
kubectl expose service prometheus-server \
  --type=LoadBalancer \
  --target-port=9090 \
  --name=prometheus-lb \
  -n prometheus

# URL lo
kubectl get svc -n prometheus
# EXTERNAL-IP copy karo — browser mein :80 pe khulega
```

**Prometheus UI check:**
```
Browser mein: http://<EXTERNAL-IP>
Status → Target Health → sab "UP" hone chahiye
```

---

## 8. Phase 4 — Application Deploy

> Yeh tumhara actual application hai jisko monitor karna hai.

`prometheus.yml` file ka content:
```yaml
apiVersion: v1
kind: Service
metadata:
  annotations:
    prometheus.io/path: /actuator/prometheus   # ← scraping endpoint
    prometheus.io/scrape: "true"               # ← scraping enable
  name: mysv-cip
spec:
  ports:
    - port: 8081
      targetPort: 8082
  selector:
    app: datastore
---
apiVersion: apps/v1
kind: Deployment
metadata:
  labels:
    app: datastore
  name: datastore-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: datastore
  template:
    metadata:
      labels:
        app: datastore
    spec:
      containers:
      - image: 8072388539/datastore:v34.0
        name: datastore
```

```bash
# Application deploy karo
kubectl apply -f prometheus.yml

# Check karo
kubectl get pods
kubectl get svc

# Prometheus mein verify karo
# Browser → Prometheus → Status → Targets
# "mysv-cip" service ka actuator/prometheus endpoint "UP" dikhna chahiye
```

---

## 9. Phase 5 — Grafana Install

```bash
# Repo add karo
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Namespace banao
kubectl create namespace grafana

# Grafana install karo
helm install grafana grafana/grafana \
  --namespace grafana \
  --set persistence.storageClassName="monitor-ebs-storage" \
  --set persistence.enabled=true \
  --set adminPassword='shiva' \
  --set service.type=LoadBalancer

# Verify
kubectl get all -n grafana

# URL lo
kubectl get svc -n grafana
# EXTERNAL-IP copy karo
```

**Browser mein login karo:**
```
URL: http://<EXTERNAL-IP>
Username: admin
Password: shiva
```

---

## 10. Phase 6 — Grafana Configure + Dashboard

### Step 1: Prometheus Data Source Add karo

```
Grafana mein:
Settings (⚙️ gear icon) → Data Sources → Add data source
→ Prometheus select karo
→ URL mein daalo: http://prometheus-server.prometheus.svc.cluster.local
→ "Save & Test" dabao
→ "Successfully queried" message aana chahiye
```

> **Yeh URL kaise kaam karta hai:**
> `prometheus-server` = service name
> `prometheus` = namespace
> `.svc.cluster.local` = Kubernetes internal DNS
> Grafana aur Prometheus dono cluster ke andar hain isliye yeh kaam karta hai

### Step 2: Readymade Dashboard Import karo

**Option A — K8S Dashboard (Recommended, classmate waala)**
```
Dashboards → + → Import
Dashboard ID: 6417
→ Load dabao
→ Prometheus data source select karo
→ Import
```

**Option B — Alternative Dashboard**
```
Dashboard ID: 15661
(zyada detailed, microservice level data)
```

**Kya dikhega import ke baad:**
```
✓ Running Pods count
✓ CPU Load per Node (graph)
✓ CPU Utilization per Node
✓ Network Traffic (Receive/Transmit)
✓ Disk Utilization by Node
✓ Pod CPU Usage
✓ Pods per Node (gauge)
✓ Workload / Total Pod / Total Nodes count
```

---

## 11. Custom Dashboard Banana

Khud ka dashboard banana ho toh:

```
Grafana → Dashboards → New → New Dashboard → Add visualization
```

### Panel types:

| Type | Use karo jab |
|------|-------------|
| **Stat** | Single number dikhana ho (jaise "16 pods running") |
| **Gauge** | Percentage dikhana ho (CPU 65%) |
| **Time series** | Time ke saath change dikhana ho (graph) |
| **Table** | Multiple rows ka data |
| **Bar chart** | Compare karna ho |

### Useful Queries:

```promql
# Running pods count
sum(kube_pod_status_phase{phase="Running"})

# CPU usage (%)
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memory used (%)
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)
  / node_memory_MemTotal_bytes * 100

# Specific namespace ke pods
count(kube_pod_info{namespace="prometheus"})

# Apne app ka data (datastore)
http_requests_total{service="mysv-cip"}

# Pod restarts
increase(kube_pod_container_status_restarts_total[1h])

# Node disk usage
(node_filesystem_size_bytes - node_filesystem_free_bytes)
  / node_filesystem_size_bytes * 100
```

### Panel banane ka flow:

```
1. "Add visualization" click karo
2. Neeche "Metrics browser" mein query daalo
3. Upar right mein visualization type choose karo (Stat / Gauge / etc.)
4. Title daalo
5. Apply → Save dashboard
```

---

## 12. Auto-Switch Playlist

Multiple dashboards automatically switch karne ke liye:

```
Grafana → Dashboards → Playlists → New playlist
```

| Setting | Value |
|---------|-------|
| Name | My Monitoring |
| Interval | 30s (ya jitna chahiye) |
| Dashboards | K8S Dashboard, Kubernetes Cluster — dono add karo |

```
Save → Playlist pe click → Start playlist
F11 (full screen) → TV mode ready!
```

**Band karne ke liye:** `Escape` ya top-right "Stop playlist"

---

## 13. Important Queries — PromQL

### Basic Queries

```promql
# Sab pods ka status
sum(kube_pod_status_phase) by (namespace)

# Running pods sirf
sum(kube_pod_status_phase{phase="Running"}) by (pod)

# Failed pods — alert ke liye
sum(kube_pod_status_phase{phase="Failed"})

# Nodes count
count(kube_node_info)
```

### CPU Queries

```promql
# Overall CPU usage %
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Per pod CPU
rate(container_cpu_usage_seconds_total{namespace!=""}[5m])

# Top CPU consuming pods
topk(5, rate(container_cpu_usage_seconds_total[5m]))
```

### Memory Queries

```promql
# Node memory used
node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes

# Memory usage %
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# Per container memory
container_memory_working_set_bytes{namespace!=""}
```

### Network Queries

```promql
# Network receive bytes
rate(node_network_receive_bytes_total[5m])

# Network transmit bytes
rate(node_network_transmit_bytes_total[5m])
```

---

## 14. Troubleshooting

### Pod "Pending" mein atka hai

```bash
kubectl describe pod <pod-name> -n prometheus
# "Events" section dekho
```

| Problem | Solution |
|---------|----------|
| `no persistent volumes available` | EBS CSI driver check karo, StorageClass verify karo |
| `Insufficient memory` | Node ka size badao (t3.large try karo) |
| `ImagePullBackOff` | Docker image name check karo |

### Prometheus Target "DOWN" hai

```bash
# Service endpoints check karo
kubectl get svc -n default

# Annotations sahi hain?
kubectl describe svc mysv-cip
# prometheus.io/scrape: "true" hona chahiye
```

### Grafana "No data" dikh raha hai

```
1. Data source test karo — Settings → Data Sources → Test
2. URL sahi hai? → http://prometheus-server.prometheus.svc.cluster.local
3. Time range check karo — "Last 30 minutes" select karo
4. Query sahi hai? → Prometheus UI mein pehle test karo
```

### Helm install fail hua

```bash
# Pehle delete karo, phir dobara install
helm uninstall prometheus -n prometheus
helm install prometheus prometheus-community/prometheus ...
```

### Sabse common commands debugging ke liye

```bash
# Sab pods ka status
kubectl get pods --all-namespaces

# Kisi pod ke logs
kubectl logs <pod-name> -n <namespace>

# Pod ke andar kya ho raha hai
kubectl describe pod <pod-name> -n <namespace>

# Services check karo
kubectl get svc --all-namespaces

# Storage check karo
kubectl get pvc --all-namespaces
```

---

## 15. Files Reference

### `storage.yml`
**Kaam:** AWS EBS StorageClass define karta hai jiska naam `monitor-ebs-storage` hai. Prometheus aur Grafana dono isi se apna data disk pe save karte hain.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: monitor-ebs-storage      # ← yeh naam Helm install mein use hoga
provisioner: ebs.csi.aws.com     # ← AWS EBS driver
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete            # ← cluster delete hone pe disk bhi delete
parameters:
  type: gp2                      # ← AWS disk type (general purpose SSD)
```

**Kab apply karo:** EBS CSI driver install karne ke baad, Prometheus install se pehle.

---

### `prometheus.yml`
**Kaam:** Datastore application ko Kubernetes mein deploy karta hai aur Prometheus ko batata hai ki isse scrape karna hai.

**Important parts:**
```yaml
annotations:
  prometheus.io/scrape: "true"         # ← Prometheus yeh dekh ke scrape karta hai
  prometheus.io/path: /actuator/prometheus  # ← kahan se data lena hai
```

**Kab apply karo:** Prometheus install ho jaane ke baad.

---

## 16. Cost Warning

> **AWS charges lagte hain! Practice ke baad cluster delete kar do.**

```bash
# Grafana + Prometheus uninstall karo
helm uninstall grafana -n grafana
helm uninstall prometheus -n prometheus

# Cluster delete karo (sab kuch band ho jaayega)
eksctl delete cluster --name my-monitoring-cluster --region us-east-1
```

**Approximate cost (agar chhod diya):**
- EKS cluster: ~$0.10/hour
- t3.medium node: ~$0.04/hour
- EBS volumes: ~$0.10/GB/month

**Yeh commands chalane ke baad koi charge nahi aayega.**

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│              QUICK COMMANDS                             │
├─────────────────────────────────────────────────────────┤
│ Sab pods dekho    kubectl get pods --all-namespaces     │
│ Prometheus UI     kubectl get svc -n prometheus         │
│ Grafana UI        kubectl get svc -n grafana            │
│ Logs dekho        kubectl logs <pod> -n <namespace>     │
│ Describe pod      kubectl describe pod <pod> -n <ns>    │
│ Storage check     kubectl get pvc --all-namespaces      │
├─────────────────────────────────────────────────────────┤
│              IMPORTANT URLs                             │
├─────────────────────────────────────────────────────────┤
│ Prometheus        http://<LB-IP>:80                     │
│ Grafana           http://<LB-IP>:80                     │
│ Grafana Login     admin / shiva                         │
│ Prometheus DS     http://prometheus-server.             │
│                   prometheus.svc.cluster.local          │
├─────────────────────────────────────────────────────────┤
│              DASHBOARD IDs                              │
├─────────────────────────────────────────────────────────┤
│ K8S Dashboard     6417                                  │
│ Alt Dashboard     15661                                 │
└─────────────────────────────────────────────────────────┘
```

---

*Document banaya gaya: AWS EKS pe Prometheus + Grafana monitoring ka complete practical guide*
