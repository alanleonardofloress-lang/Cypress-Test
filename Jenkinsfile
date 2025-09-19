pipeline {
    agent any

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
}
