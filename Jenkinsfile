pipeline {
    agent any

    options {
        ansiColor('xterm')   // habilita colores en consola
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/alanleonardofloress-lang/Cypress-Test.git'
            }
        }

        stage('Install dependencies') {
            steps {
                sh 'npm install'
            }
        }

        stage('Run Cypress tests') {
            steps {
                sh 'npx cypress run'
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
        }
    }
}
