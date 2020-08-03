docker_build('daemon-chore-slack-nandy-io', './daemon')

k8s_yaml(kustomize('.'))

k8s_resource('daemon', port_forwards=['26744:5678'])