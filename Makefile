.PHONY: install remove reset tag

install:
	kubectl create namespace chore-slack-nandy-io

remove:
	kubectl delete namespace chore-slack-nandy-io

reset: remove install

tag:
	-git tag -a "v$(VERSION)" -m "Version $(VERSION)"
	git push origin --tags
