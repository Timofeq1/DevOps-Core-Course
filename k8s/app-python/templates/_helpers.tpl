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
Resolve ConfigMap name for file-based configuration.
*/}}
{{- define "app-python.fileConfigMapName" -}}
{{- printf "%s-config" (include "common.fullname" .) -}}
{{- end -}}

{{/*
Resolve ConfigMap name for environment variable configuration.
*/}}
{{- define "app-python.envConfigMapName" -}}
{{- printf "%s-env" (include "common.fullname" .) -}}
{{- end -}}

{{/*
Resolve PVC name for persistent application data.
*/}}
{{- define "app-python.pvcName" -}}
{{- printf "%s-data" (include "common.fullname" .) -}}
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
