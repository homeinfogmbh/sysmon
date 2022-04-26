FILE_LIST = ./.installed_files.txt

.PHONY: pull push clean install uninstall jsonschema javascript

default: | pull clean install jsonschema javascript

install:
	@ ./setup.py install --record $(FILE_LIST)

uninstall:
	@ while read FILE; do echo "Removing: $$FILE"; rm "$$FILE"; done < $(FILE_LIST)

clean:
	@ rm -Rf ./build

pull:
	@ git pull

push:
	@ git push

jsonschema:
	@ mkdir -p /srv/http/de/homeinfo/jsonschema/sysmon
	@ install -t /srv/http/de/homeinfo/jsonschema/sysmon jsonschema/*.schema.json

javascript:
	@ mkdir -p /srv/http/de/homeinfo/javascript
	@ install -t /srv/http/de/homeinfo/javascript sysmon.mjs
