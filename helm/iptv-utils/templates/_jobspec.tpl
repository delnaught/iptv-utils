{{- define "iptv-utils.jobspec" -}}
  template:
    metadata:
      {{- with .Values.jobAnnotations }}
      annotations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      labels:
        {{- with .Values.jobLabels }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "iptv-utils.serviceAccountName" . }}
      {{- with .Values.podSecurityContext }}
      securityContext:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      restartPolicy: Never
      initContainers:
        - name: git
          image: "{{ .Values.gitImage.repository }}:{{ .Values.gitImage.tag }}"
          imagePullPolicy: {{ .Values.gitImage.pullPolicy }}
          command: ["sh", "-c", "rm -rf {{ .Values.env.epg_local }} && git clone --depth 1 {{ .Values.env.epg_upstream }} {{ .Values.env.epg_local }}"]
          env:
            {{- include "iptv-utils.env" . | nindent 12 }}
          {{- with .Values.volumeMounts }}
          volumeMounts:
            {{- toYaml . | nindent 12 }}
          {{- end }}
        - name: util
          image: "{{ .Values.utilImage.repository }}:{{ .Values.utilImage.tag }}"
          imagePullPolicy: {{ .Values.utilImage.pullPolicy }}
          command: ["python3", "generate.py"]
          env:
            {{- include "iptv-utils.env" . | nindent 12 }}
          {{- with .Values.volumeMounts }}
          volumeMounts:
            {{- toYaml . | nindent 12 }}
          {{- end }}
      containers:
        - name: epg
          image: "{{ .Values.epgImage.repository }}:{{ .Values.epgImage.tag }}"
          imagePullPolicy: {{ .Values.epgImage.pullPolicy }}
          command: ["sh", "-c", "cd {{ .Values.env.epg_local }} && npm install && npm run grab -- --channels={{- .Values.env.epg_xml}} --output={{- .Values.env.guide_xml}}"]
          env:
            {{- include "iptv-utils.env" . | nindent 12 }}
          {{- with .Values.volumeMounts }}
          volumeMounts:
            {{- toYaml . | nindent 12 }}
          {{- end }}
      {{- with .Values.volumes }}
      volumes:
        {{- toYaml . | nindent 8 }}
      {{- end }}
{{- end }}
