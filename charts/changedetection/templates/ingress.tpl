{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ .Values.name }}
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt
    external-dns.alpha.kubernetes.io/host: {{ .Values.ingress.hostname }}
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - {{ .Values.ingress.hostname }}
      secretName: {{ .Values.name }}-cert
  rules:
    - host: {{ .Values.ingress.hostname }}
      http:
        paths:
          - path: /
            pathType: ImplementationSpecific
            backend:
              service:
                name: {{ .Values.name }}
                port:
                  name: http
{{- end }}
