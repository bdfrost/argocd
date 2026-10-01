apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Values.name }}
  labels:
    app.kubernetes.io/name: {{ .Values.name }}
spec:
  replicas: {{ .Values.replicaCount }}
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app.kubernetes.io/name: {{ .Values.name }}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {{ .Values.name }}
    spec:
      containers:
        - name: changedetection
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.targetPort }}
              protocol: TCP
          env:
            - name: TZ
              value: {{ .Values.timezone | quote }}
            - name: BASE_URL
              value: {{ .Values.baseURL | quote }}
            - name: LISTEN_HOST
              value: "0.0.0.0"
            - name: ALLOW_IANA_RESTRICTED_ADDRESSES
              value: {{ .Values.allowIanaRestrictedAddresses | quote }}
          startupProbe:
            httpGet:
              path: /
              port: http
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 30
          readinessProbe:
            httpGet:
              path: /
              port: http
            periodSeconds: 10
            timeoutSeconds: 5
          livenessProbe:
            httpGet:
              path: /
              port: http
            periodSeconds: 30
            timeoutSeconds: 5
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          volumeMounts:
            - name: datastore
              mountPath: /datastore
      volumes:
        - name: datastore
          persistentVolumeClaim:
            claimName: {{ .Values.name }}-data
