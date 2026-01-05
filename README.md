# Flask + MongoDB on Kubernetes (Minikube)

This README contains the **complete submission** for the DevOps Intern Assignment, including Dockerfile, build & push instructions, Kubernetes YAML files, deployment steps, explanations, design choices, and testing scenarios.

---

## 1. Dockerfile for Flask Application

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

CMD ["python", "app.py"]
```

---

## 2. Build & Push Docker Image

### Build Image
```bash
docker build -t <dockerhub-username>/flask-mongo-app .
```

### Login to DockerHub
```bash
docker login
```

### Push Image
```bash
docker push <dockerhub-username>/flask-mongo-app
```

---

## 3. Kubernetes YAML Files

### 3.1 MongoDB Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mongo-secret
type: Opaque
data:
  mongo-user: YWRtaW4=
  mongo-password: cGFzc3dvcmQ=
```

---

### 3.2 Persistent Volume
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: mongo-pv
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /data/mongo
```

---

### 3.3 Persistent Volume Claim
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mongo-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

---

### 3.4 MongoDB StatefulSet
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
spec:
  serviceName: mongodb-service
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:6.0
        ports:
        - containerPort: 27017
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          valueFrom:
            secretKeyRef:
              name: mongo-secret
              key: mongo-user
        - name: MONGO_INITDB_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mongo-secret
              key: mongo-password
        volumeMounts:
        - name: mongo-storage
          mountPath: /data/db
        resources:
          requests:
            cpu: "0.2"
            memory: "250Mi"
          limits:
            cpu: "0.5"
            memory: "500Mi"
  volumeClaimTemplates:
  - metadata:
      name: mongo-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Gi
```

---

### 3.5 MongoDB Service (ClusterIP)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: mongodb-service
spec:
  selector:
    app: mongodb
  ports:
    - port: 27017
      targetPort: 27017
  type: ClusterIP
```

---

### 3.6 Flask Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: flask
  template:
    metadata:
      labels:
        app: flask
    spec:
      containers:
      - name: flask
        image: <dockerhub-username>/flask-mongo-app
        ports:
        - containerPort: 5000
        env:
        - name: MONGODB_URI
          value: mongodb://admin:password@mongodb-service:27017/
        resources:
          requests:
            cpu: "0.2"
            memory: "250Mi"
          limits:
            cpu: "0.5"
            memory: "500Mi"
```

---

### 3.7 Flask Service (NodePort)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: flask-service
spec:
  selector:
    app: flask
  ports:
    - port: 5000
      targetPort: 5000
      nodePort: 30007
  type: NodePort
```

---

### 3.8 Horizontal Pod Autoscaler
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: flask-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: flask-app
  minReplicas: 2
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 4. Deployment Steps (Minikube)

```bash
minikube start
kubectl apply -f mongo-secret.yaml
kubectl apply -f mongo-pv.yaml
kubectl apply -f mongo-pvc.yaml
kubectl apply -f mongo-statefulset.yaml
kubectl apply -f mongo-service.yaml
kubectl apply -f flask-deployment.yaml
kubectl apply -f flask-service.yaml
kubectl apply -f flask-hpa.yaml
```

Access the app:
```bash
minikube service flask-service --url
```

---

## 5. DNS Resolution in Kubernetes

Kubernetes uses CoreDNS for service discovery. Each Service is reachable via:

```
<service-name>.<namespace>.svc.cluster.local
```

The Flask app connects to MongoDB using:
```
mongodb-service.default.svc.cluster.local
```

This removes hardcoded IPs and enables reliable inter-pod communication.

---

## 6. Resource Requests & Limits

- **Requests** guarantee minimum resources for scheduling.
- **Limits** prevent resource starvation.

Configured values:
- Request: 0.2 CPU, 250Mi
- Limit: 0.5 CPU, 500Mi

---

## 7. Design Choices

- **StatefulSet for MongoDB**: stable identity and persistent storage
- **Deployment for Flask**: stateless and scalable
- **ClusterIP for MongoDB**: internal-only access
- **NodePort for Flask**: simple Minikube exposure

**Alternatives considered**:
- Deployment for MongoDB (rejected: no stable storage)
- LoadBalancer (rejected: not required for local Minikube)

---

## 8. Testing Scenarios (Cookie Point)

### Database Testing
- Inserted data using POST requests
- Restarted MongoDB pod
- Verified data persistence via PVC

### Autoscaling Testing
```bash
kubectl run load-generator --image=busybox -it --rm -- /bin/sh
while true; do wget -q -O- http://flask-service:5000; done
```

**Observed**:
- CPU crossed 70%
- Pods scaled from 2 to 4
- Scaled back after stopping load

**Issues encountered**:
- Metrics-server startup delay (resolved by re-enabling addon)

---
## 📸 Autoscaling & Deployment Evidence

### Minikube Cluster Status
![Minikube Nodes](screenshots/01-minikube-nodes.png)

### Running Pods
![Pods](screenshots/01-minikube-nodes.png)

### Services
![Services](screenshots/01-minikube-nodes.png)

### Flask Application Response
![Flask App](screenshots/04-flask-app-response.png)

### MongoDB Interaction
![MongoDB](screenshots/05-mongodb-interaction.png)

### Horizontal Pod Autoscaler
![HPA](screenshots/06-hpa-created.png)

### Load Test
![Load Test](screenshots/07-load-test-running.png)

### Autoscaling in Action
![Autoscaling](screenshots/08-autoscaling-pods.png)

### Resource Metrics
![Metrics](screenshots/09-metrics-cpu-memory.png)

## ✅ Final Outcome

✔ Flask app deployed
✔ MongoDB secured with authentication
✔ Persistent storage configured
✔ DNS resolution working
✔ HPA autoscaling verified

---


