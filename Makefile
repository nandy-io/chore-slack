VERSION?=0.3
TILT_PORT=26776
.PHONY: up down integrate disintegrate tag untag

settings:
	kubectl -n chore-slack-nandy-io get configmap config -o jsonpath='{.data.settings\.yaml}' > config/settings.yaml

integrate:
	cp daemon/forms/person.fields.yaml ../people/config/integration_chore-slack.nandy.io_person.fields.yaml

disintegrate:
	rm ../people/config/integration_chore-slack.nandy.io_person.fields.yaml

up: integrate
	mkdir -p config
	echo "- op: add\n  path: /spec/template/spec/volumes/0/hostPath/path\n  value: $(PWD)/config" > tilt/config.yaml
	if test ! -f config/settings.yaml; then echo "\n!!! need settings !!!\n" && exit 1; fi
	kubectx docker-desktop
	tilt --port $(TILT_PORT) up

down: disintegrate
	kubectx docker-desktop
	tilt down

tag:
	-git tag -a "v$(VERSION)" -m "Version $(VERSION)"
	git push origin --tags

untag:
	-git tag -d "v$(VERSION)"
	git push origin ":refs/tags/v$(VERSION)"
