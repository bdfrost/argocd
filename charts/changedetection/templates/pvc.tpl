{{- if .Values.persistence.enabled }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ .Values.name }}-data
spec:
  accessModes:
    - {{ .Values.persistence.accessMode }}
  storageClassName: {{ .Values.persistence.storageClass }}
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
{{- end }}
