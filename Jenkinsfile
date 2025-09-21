pipeline {
    agent any

    options {
        ansiColor('xterm')   // habilita colores en consola
    }

    environment {
        LC_ALL = 'C.UTF-8'
        LANG   = 'C.UTF-8'
    }

    parameters {
        choice(
            name: 'TEST_SUITE',
            choices: ['regression', 'smoke_test_bse'],
            description: 'Seleccionar suite de Cypress a ejecutar'
        )
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/alanleonardofloress-lang/Cypress-Test.git'
            }
        }

stage('List files') {
    steps {
        sh 'echo " Contenido de cypress/e2e:"'
        sh 'ls -R cypress/e2e'
    }
}

        stage('Install dependencies') {
            steps {
                sh 'npm install'
            }
        }

        stage('Run Selected Suite') {
    steps {
        sh "npx cypress run --browser chrome --headless --spec \"cypress/e2e/${params.TEST_SUITE}/*.cy.js\""
    }
}

    }

    post {
        success {
            echo '\u001B[32m✅ Pipeline finalizado con éxito!\u001B[0m'
        }
        failure {
            echo '\u001B[31m❌ Pipeline falló. Revisar logs de Cypress.\u001B[0m'
        }
        always {
            echo '\u001B[34m📦 Pipeline terminado (éxito o fallo).\u001B[0m'
            archiveArtifacts artifacts: 'cypress/screenshots/**/*.png', allowEmptyArchive: true
            archiveArtifacts artifacts: 'cypress/videos/**/*.mp4', allowEmptyArchive: true
        }
    }
}

