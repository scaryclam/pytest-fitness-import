create_env:
	virtualenv fitness-env

install_deps:
	bash -c 'source fitness-env/bin/activate && pip install -r requirements.txt'

install_env: create_env	install_deps
