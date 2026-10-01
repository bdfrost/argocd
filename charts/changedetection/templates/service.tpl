apiVersion: v1
kind: Service
metadata:
  name: {{ .Values.name }}
  labels:
    app.kubernetes.io/name: {{ .Values.name }}
spec:
  type: ClusterIP
  ipFamilies:
    - IPv4
  ipFamilyPolicy: SingleStack
  selector:
    app.kubernetes.io/name: {{ .Values.name }}
  ports:
    - name: http
      port: 80
      targetPort: http
      protocol: TCP
