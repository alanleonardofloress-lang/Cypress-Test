pipeline {
    agent any

    options {
        ansiColor('xterm')
    }

    environment {
        LC_ALL = 'C.UTF-8'
        LANG   = 'C.UTF-8'
        PYTHON_HOME = 'C:\\Users\\aflores\\mi-proyecto-cypress\\venv\\Scripts\\python.exe'
        PROJECT_DIR = "${WORKSPACE}"
    }

    parameters {
        choice(
            name: 'TEST_TYPE',
            choices: ['CYPRESS', 'SELENIUM'],
            description: 'Seleccionar tipo de test a ejecutar'
        )
        choice(
            name: 'TEST_SUITE',
            choices: ['regression', 'smoke_test_bse'],
            description: 'Seleccionar suite de Cypress (solo si TEST_TYPE = CYPRESS)'
        )
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/alanleonardofloress-lang/Cypress-Test.git'
            }
        }

        stage('Mostrar parámetros seleccionados') {
            steps {
                echo "Tipo de test seleccionado: ${params.TEST_TYPE}"
                echo "Suite de Cypress: ${params.TEST_SUITE}"
            }
        }

        stage('Instalar dependencias') {
            steps {
                script {
                    if (params.TEST_TYPE.equalsIgnoreCase('CYPRESS')) {
                        echo 'Instalando dependencias de Cypress...'
                        sh 'npm install'
                    } else {
                        echo 'Instalando dependencias de Selenium...'
                        bat """
                            cd %PROJECT_DIR%
                            %PYTHON_HOME% -m pip install --upgrade pip
                            %PYTHON_HOME% -m pip install -r requirements.txt
                        """
                    }
                }
            }
        }

        stage('Ejecutar tests') {
            steps {
                script {
                    if (params.TEST_TYPE.equalsIgnoreCase('CYPRESS')) {
                        echo 'Ejecutando suite de Cypress...'
                        sh "npx cypress run --browser chrome --headless --spec \"cypress/e2e/${params.TEST_SUITE}/*.cy.js\""
                    } else {
                        echo 'Ejecutando test Selenium...'
                        echo "Ruta de Python: ${env.PYTHON_HOME}"
                        echo "Workspace actual: ${env.WORKSPACE}"

                        bat """
                            echo === Verificando entorno Python ===
                            %PYTHON_HOME% --version
                            %PYTHON_HOME% -m pip show selenium
                            echo === Ejecutando test Bantotal ===
                            cd %PROJECT_DIR%
                            %PYTHON_HOME% -m selenium_local.test_bantotal
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline finalizado con éxito.'
        }
        failure {
            echo 'Pipeline falló. Revisar logs.'
        }
        always {
            echo 'Pipeline terminado (éxito o fallo).'
            archiveArtifacts artifacts: 'cypress/screenshots/**/*.png', allowEmptyArchive: true
            archiveArtifacts artifacts: 'cypress/videos/**/*.mp4', allowEmptyArchive: true
            archiveArtifacts artifacts: 'selenium_local/**/*.png', allowEmptyArchive: true
            archiveArtifacts artifacts: 'selenium_local/**/*.log', allowEmptyArchive: true
        }
    }
}
