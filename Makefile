install: web2py pydeps postgresql additional

virt-env:
	sudo apt-get install virtualenvwrapper
	mkvirtualenv pci --python=`which python3.12`

web2py:
	cd .. ; git clone --recurse-submodules \
		--depth=3 \
		--branch v3.0.11+pci-patches \
		https://github.com/pci-dev/web2py
	ln -s $(PWD) ../web2py/applications/pci
	cp utils/routes.py ../web2py/

pydeps:
	pip install -r requirements.txt

postgresql:
	sudo apt-get install -y postgresql postgresql-contrib

additional:
	sudo apt-get install -y libimage-exiftool-perl

db:
	$(psql) -c "CREATE ROLE pci_admin WITH LOGIN PASSWORD 'admin4pci'"
	$(psql) -c "CREATE DATABASE main"
	$(psql) main -c "CREATE EXTENSION unaccent"
	$(psql) main < sql_dumps/pci_evolbiol_test.sql
	$(psql) main < sql_dumps/pci_evolbiol_test_data0.sql
	$(psql) main < sql_dumps/insert_default_help_texts.sql
	$(psql) main < sql_dumps/insert_default_mail_templates.sql
	$(psql) main < sql_dumps/t_status_article.sql

db.clean:
	$(psql) -c "drop database if exists main"
	$(psql) -c "drop role if exists pci_admin"

db.admin:
	echo "map_admin $$USER postgres" | sudo tee -a /etc/postgresql/*/main/pg_ident.conf
	sudo sed -i '/local *all *postgres *peer/ s/$$/ map=map_admin/' /etc/postgresql/*/main/pg_hba.conf
	sudo systemctl restart postgresql

psql = psql -q -U postgres -v "ON_ERROR_STOP=1"

start start.debug:
	../web2py/web2py.py --password pci $(log) &

stop:
	@PID=`ps ax -o pid,args | grep web2py.py | grep -v grep | awk '{print $$1}'` ;\
	[ "$$PID" ] && kill $$PID && echo killed $$PID || echo "not running"

start: conf init

conf:	private/appconfig.ini

init:	logo

logo:	static/images/background.png \
	static/images/small-background.png

private/% static/%:
	cd $(dir $@) && cp sample.$(notdir $@) $(notdir $@)

start: log = > /dev/null


test.install.selenium: install.selenium install.firefox

install.selenium:
	pip install -r tests/requirements.txt

install.chromium:
	sudo apt install chromium-chromedriver

install.firefox:
	sudo apt install firefox-geckodriver

test.install: test.install.selenium

test.setup: test.db

test.db:
	$(psql) main < sql_dumps/insert_test_users.sql

test.db.rr:
	$(psql) main -c "delete from mail_templates"
	$(psql) main < sql_dumps/insert_default_mail_templates_pci_RR.sql

test.reset:	reset set.conf.rr.false
test.reset.rr:	reset set.conf.rr.true test.db.rr
reset:		stop db.clean db test.setup start

set.conf.rr.%:
	rm -f languages/default.py
	sed -i '/^registered_reports/ s/=.*/= $*/' private/appconfig.ini
	sed -i '/^scheduled_submissions/ s/=.*/= $*/' private/appconfig.ini

test.full test.basic test.medium test.scheduled-track: delete.external.user

test.full:		test_full.py
test.basic:		test_basic.py
test.medium:		test_medium.py
test.scheduled-track:	test_scheduled_track.py

test.full test.basic test.medium test.scheduled-track: test.clean


test.create-article:
	cd tests ; uv run pytest -k "basic and User_submits"

test.review.registered-user:
	cd tests; uv run pytest -v -k "review_article and Reviewer"

test.review.external:
	cd tests; uv run pytest -v -k "review_article and External"

test.review.no-upload:
	cd tests; RR_SCHEDULED_TRACK=1 \
	uv run pytest -v -k "review_article and Reviewer"

test_%:
	(cd tests; uv run pytest -xv $@)

delete.external.user:
	$(psql) main -c "delete from auth_user where first_name='Titi';"

test.clean:
	pkill -9 -ef 'geckodriver[ ]|marionette[ ]' || true

coar.refresh:
	touch modules/app_modules/coar_notify.py

reload.web2py:
	touch ../../wsgihandler.py

recreate.v_article:
	~/all-pci-db.sh | while read db; do \
	psql -h mydb1 -p 33648 -U peercom $$db \
		< utils/re-create_v_article.sql; \
	done

setup.new-pci: dirs = errors/ uploads/ sessions/ databases/ cron/ tmp/
setup.new-pci:
	mkdir -p $(dirs)
	chgrp www-data $(dirs) private
	chmod g+w $(dirs)
	chmod g+r private
	ln -s default_base.py languages/default.py

api:
	cp -f utils/api/sparse-checkout .git/info/
	git sparse-checkout init
	ln -sf api.py controllers/default.py
	mkdir -p models && \
	ln -sf ../utils/api/db_plug.py models/
	ln -sf utils/api/README.md ./
	find . | grep -v .git

api.dismount:
	\rm -f controllers/default.py models/db_plug.py
	git sparse-checkout disable

check.static:
	@git diff --stat `git describe --tag --abbrev=0` \
	| grep static/ || echo "no update needed"

build:
	docker build -t pci .

dev: build
	docker kill pci || echo "No pci container running"
	docker run --rm -d --name pci -p 8080:8000 pci
	docker exec -i pci psql -U postgres -d main -f /dev/stdin < sql_dumps/additional_test_data_insert.psql
	docker attach pci

watch:
	find . -type f | grep '.py' | entr -r make dev

# Docker test targets

test.docker.reset:
	docker exec pci make test.reset

test.docker.basic:
	docker exec pci make test.basic

test.docker.medium:
	docker exec pci make test.medium

test.docker.full:
	docker exec pci make test.full

test.docker.unittest:
	docker run \
		--rm \
		--volume $(PWD)/tests:/app/tests \
		--volume $(PWD)/controllers:/app/controllers \
		pci \
		bash -c "cd tests/unit_tests && PYTHONPATH=../..:../../modules uv run pytest"

test.docker.selenium:
	docker exec pci sh -c "cd tests && pytest $(ARGS)"

log:
	@git log --merges --format=%s \
		`git describe --tag --abbrev=0`..
