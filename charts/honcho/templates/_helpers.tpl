{{- define "honcho.name" -}}
{{- .Values.name | default .Chart.Name -}}
{{- end -}}

{{- define "honcho.labels" -}}
app.kubernetes.io/name: {{ include "honcho.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end -}}

{{- define "honcho.dbUri" -}}
postgresql+psycopg://{{ .Values.config.database.user }}:{{ .Values.config.database.password }}@{{ include "honcho.name" . }}-postgres:5432/{{ .Values.config.database.name }}
{{- end -}}
