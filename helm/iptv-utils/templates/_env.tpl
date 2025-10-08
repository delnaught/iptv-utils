{{- define "iptv-utils.env" -}}
- name: EPG_UPSTREAM
  value: {{ .Values.env.epg_upstream }}
- name: EPG_LOCAL
  value: {{ .Values.env.epg_local }}
- name: EPG_XML
  value: {{ .Values.env.epg_xml }}
- name: GUIDE_XML
  value: {{ .Values.env.guide_xml }}
- name: PLAYLIST_M3U
  value: {{ .Values.env.playlist_m3u }}
{{- end }}
