{{- define "iptv-utils.jobspec" -}}
  template:
    metadata:
      {{- with .Values.jobAnnotations }}
      annotations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      labels:
        {{- include "iptv-utils.labels" . | nindent 8 }}
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
        - name: generate
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          command: ["python", "generate.py"]
          env:
            - name: LIVETV_DIR
              value: "/livetv"
            - name: EPG_XML
              value: "/livetv/channels.xml"
          volumeMounts:
            - name: livetv
              mountPath: "/livetv"
      containers:
        - name: fetch
          image: "{{ .Values.epgImage.repository }}:{{ .Values.epgImage.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          command: ["npm", "run", "grab", "--", "--channels=/livetv/channels.xml", "--output=/livetv/guide.xml"]
          {{- with .Values.env }}
          env:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.volumeMounts }}
          volumeMounts:
            {{- toYaml . | nindent 12 }}
          {{- end }}
      {{- with .Values.volumes }}
      volumes:
        {{- toYaml . | nindent 8 }}
      {{- end }}
{{- end }}
