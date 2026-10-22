pipeline {
  agent any

  triggers { githubPush() }

  options {
    timestamps()
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '10'))
  }

  environment {
    APP_HOST = '79.76.22.169'
    APP_USER = 'opc'
    APP_HOME = '/opt/practice-b'
    APP_DIR  = '/opt/practice-b/app'
    VENV     = '/opt/practice-b/venv'
    REPO_URL = 'https://github.com/abdulzafermobile/practice-b-inventory-api.git'
    SSH_OPTS = '-o StrictHostKeyChecking=accept-new -o BatchMode=yes'
  }

  stages {

    stage('Fetch code on server') {
      steps {
        sshagent(credentials: ['ssh-oci-vm-key']) {
          sh '''
            set -eu
            T="$APP_USER@$APP_HOST"
            if ssh $SSH_OPTS $T "[ -d $APP_DIR/.git ]"; then
              ssh $SSH_OPTS $T "cd $APP_DIR && git fetch --depth 1 origin main && git reset --hard origin/main"
            else
              ssh $SSH_OPTS $T "git clone --depth 1 --branch main $REPO_URL $APP_DIR"
            fi
            ssh $SSH_OPTS $T "cd $APP_DIR && git log -1 --oneline"
          '''
        }
      }
    }

    stage('Install dependencies') {
      steps {
        sshagent(credentials: ['ssh-oci-vm-key']) {
          sh '''
            set -eu
            T="$APP_USER@$APP_HOST"
            # Create the venv only the first time
            ssh $SSH_OPTS $T "[ -x $VENV/bin/python ] || python3.11 -m venv $VENV"
            # Install exactly what requirements.txt lists
            ssh $SSH_OPTS $T "$VENV/bin/pip install --quiet --upgrade pip && $VENV/bin/pip install --quiet -r $APP_DIR/requirements.txt"
            ssh $SSH_OPTS $T "$VENV/bin/pip freeze"
          '''
        }
      }
    }

    stage('Restart service') {
      steps {
        sshagent(credentials: ['ssh-oci-vm-key']) {
          sh '''
            set -eu
            T="$APP_USER@$APP_HOST"
            # Tell the app which build it is
            ssh $SSH_OPTS $T "echo APP_BUILD=$BUILD_NUMBER > $APP_HOME/build.env"

            # Install/refresh the unit file and restart
            ssh $SSH_OPTS $T "sudo cp $APP_DIR/deploy/practice-b.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable practice-b && sudo systemctl restart practice-b"

            # A restart can 'succeed' and crash 2 seconds later: wait, then check
            ssh $SSH_OPTS $T "sleep 3; systemctl is-active --quiet practice-b || { sudo journalctl -u practice-b -n 30 --no-pager; exit 1; }"
            ssh $SSH_OPTS $T "curl -fsS http://127.0.0.1:5001/healthz"

            # Nginx config: validate first, then reload
            ssh $SSH_OPTS $T "sudo cp $APP_DIR/deploy/practice-b.conf /etc/nginx/conf.d/practice-b.conf && sudo nginx -t && sudo systemctl reload nginx"
          '''
        }
      }
    }

    stage('Verify from outside') {
      steps {
        sh '''
          set -eu
          curl -fsS --max-time 15 http://$APP_HOST:8082/healthz | grep -q "\\\"build\\\":\\\"$BUILD_NUMBER\\\""
          curl -fsS --max-time 15 http://$APP_HOST:8082/api/items
          echo
          echo "API is live on build $BUILD_NUMBER"
        '''
      }
    }
  }
}
