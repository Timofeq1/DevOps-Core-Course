{{/*
Resolve service account name for this chart.
*/}}
{{- define "app-python.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "common.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/*
Resolve secret name for app credentials.
*/}}
{{- define "app-python.secretName" -}}
{{- default (printf "%s-secret" (include "common.fullname" .)) .Values.secret.name -}}
{{- end -}}

{{/*
Common non-secret env vars rendered via include for DRY usage.
*/}}
{{- define "app-python.envVars" -}}
- name: APP_ENV
  value: {{ .Values.appConfig.environment | quote }}
- name: LOG_LEVEL
  value: {{ .Values.appConfig.logLevel | quote }}
{{- end -}}
