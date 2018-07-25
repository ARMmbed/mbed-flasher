echo "Start to build"


properties ([
    buildDiscarder(
        logRotator(
            artifactDaysToKeepStr: '',
            artifactNumToKeepStr: '',
            daysToKeepStr: '30',
            numToKeepStr: '100'
        )
    ),
    disableConcurrentBuilds()
])


parallelSteps = [:]
parallelSteps['Rpi3'] = streamStep('Rpi3', 'mbed-flasher-linux')
parallelSteps['linux-nuc'] = streamStep('linux-nuc', 'oul_ext_lin_nuc')
parallelSteps['windows'] = streamStep('windows', 'mbed-flasher-windows')


def streamStep(nodeType, nodeName) {
    return {
        node(nodeName) {
            deleteDir()

            try {
                baseBuild(nodeType)
            } catch(err) {
                throw err
            } finally {
                // clean up
                step([$class: 'WsCleanup'])
            }
        }
    }
}


def baseBuild(nodeType) {
    dir('mbed-flasher') {
        // checkout scm
        echo "checkout scm start"

        def scmVars = checkout scm
        env.GIT_COMMIT_HASH = scmVars.GIT_COMMIT

        if (isUnix()) {
            unittest(nodeType, "py2")

            unittest(nodeType, "py3")

            postBuild()
        }
        else {
            winTest("py2")

            winTest("py3")
        }

        if (nodeType =='linux-nuc'){
            linux_pylint_check()
        }
    }
}


def setBuildStatus(String state, String context, String message) {
    step([
        $class: "GitHubCommitStatusSetter",
        reposSource: [
            $class: "ManuallyEnteredRepositorySource",
            url: "https://github.com/ARMmbed/mbed-flasher.git"
        ],
        contextSource: [
            $class: "ManuallyEnteredCommitContextSource",
            context: context
        ],
        errorHandlers: [[
            $class: "ChangingBuildStatusErrorHandler",
            result: "UNSTABLE"
        ]],
        commitShaSource: [
            $class: "ManuallyEnteredShaSource",
            sha: env.GIT_COMMIT_HASH
        ],
        statusResultSource: [
            $class: 'ConditionalStatusResultSource',
            results: [
                [
                    $class: 'AnyBuildResult',
                    message: message,
                    state: state
                ]
            ]
        ]
    ])
}


def unittest(nodeType, String pythonVersion) {
    catchError {
        stage ("${nodeType} ${pythonVersion}") {
            echo "set ${pythonVersion} github status"
            String buildName = "${nodeType} ${pythonVersion} test"
            setBuildStatus('PENDING', "${buildName}", 'test start')
            try {
                if (pythonVersion == "py3") {
                    // create python 3 venv
                    if (nodeType=="Rpi3") {
                        sh """
                            set -e
                            python3 -m venv .py3venv --without-pip
                            . .py3venv/bin/activate
                            curl https://bootstrap.pypa.io/get-pip.py | python
                            deactivate
                        """
                    } else {
                        sh """
                            set -e
                            python3 -m venv .py3venv
                        """
                    }

                    // create python 3 venv
                    sh """
                        set -e
                        . .py3venv/bin/activate
                        pip install coverage mock astroid==1.5.3 pylint==1.7.2 setuptools --upgrade
                        id
                        pip freeze
                        python setup.py install
                        coverage run -m unittest discover -s test -vvv
                        coverage html
                        coverage xml
                        deactivate
                    """
                } else {
                    // create python2 venv, do installation and run tests
                    sh """
                        set -e
                        virtualenv --python=../usr/bin/python .py2venv --no-site-packages
                        . .py2venv/bin/activate
                        id
                        pip install coverage mock astroid==1.5.3 pylint==1.7.2
                        pip freeze
                        python setup.py install
                        coverage run -m unittest discover -s test -vvv
                        coverage html --include='*mbed_flasher*' --directory=logs
                        coverage xml --include='*mbed_flasher*'
                        deactivate
                    """
                }
                setBuildStatus('SUCCESS', "${buildName}", "test done")
            } catch (err) {
                echo "Caught exception: ${err}"
                setBuildStatus('FAILURE', "${buildName}", "test failed")
                throw err
            }
        }
    }
}


def linux_pylint_check() {
    stage ("linux pylint") {
        // execute pylint check shell (only linux)
        echo "python 2 pylint check started"
        sh """
            . .py2venv/bin/activate
            pylint --version
            ./run_pylint.sh | tee logs/pylint.log
            deactivate
        """

        echo "python3 pylint check started"
        sh """
            . .py3venv/bin/activate
            pylint --version
            ./run_pylint.sh | tee logs/pylint3.log
            deactivate
        """

        // publish warnings
        step([
            $class: 'WarningsPublisher',
            consoleParsers: [
                [
                    parserName: 'GNU Make + GNU C Compiler (gcc)'
                ]
            ],
            parserConfigurations: [
                [
                    parserName: 'PyLint',
                    pattern: '**/pylint.log'
                ]
            ],
            unstableTotalAll: '0',
            failedTotalAll: '0',
            parserConfigurations: [
                [
                    parserName: 'PyLint',
                    pattern: '**/pylint3.log'
                ]
            ],
            unstableTotalAll: '0',
            failedTotalAll: '0'
        ])
    }
}


def winTest(String pythonVersion) {
    catchError {
        stage ("win ${pythonVersion}") {
            echo "set ${pythonVersion} github status"
            String buildName = "windows ${pythonVersion} test"
            setBuildStatus('PENDING', "${buildName}", 'test start')
            try {
                if (pythonVersion == "py3") {
                    // create python 3 venv
                    echo 'hello windows py3 starts'
                    bat """
                        c:\\Python36\\python.exe -m venv py3venv || goto :error
                        echo "Activating venv"
                        call py3venv\\Scripts\\activate.bat || goto :error
                        pip install coverage mock || goto :error
                        if %errorlevel% neq 0 exit /b %errorlevel%
                        pip freeze
                        python setup.py install  || goto :error
                        coverage run -m unittest discover -s test -vvv || goto :error
                        coverage html & coverage xml || goto :error
                        deactivate

                        :error
                        echo "Failed with error %errorlevel%"
                        exit /b %errorlevel%
                    """
                } else {
                    // create python2 venv, do installation and run tests
                    echo 'hello windows py2 starts'
                    bat """
                        virtualenv --python=c:\\Python27\\python.exe py2venv --no-site-packages || goto :error
                        echo "Activating venv"
                        call py2venv\\Scripts\\activate.bat || goto :error
                        pip install coverage mock || goto :error
                        pip freeze
                        python setup.py install || goto :error
                        coverage run -m unittest discover -s test -vvv || goto :error
                        coverage html & coverage xml || goto :error
                        deactivate

                        :error
                        echo "Failed with error %errorlevel%"
                        exit /b %errorlevel%
                    """
                }
                setBuildStatus('SUCCESS', "${buildName}", "test done")
            } catch (err) {
                echo "Caught exception: ${err}"
                setBuildStatus('FAILURE', "${buildName}", "test failed")
                throw err
            }
        }
    }
}


def postBuild() {
    stage ("postBuild") {
        // Archive artifacts
        catchError {
            // nothing to archive
            archiveArtifacts artifacts: "logs/*.*"
        }

        // Publish cobertura
        catchError {
            step([
                $class: 'CoberturaPublisher',
                coberturaReportFile: 'coverage.xml'
            ])
        }

        // Publish HTML reports
        publishHTML(target: [
            allowMissing: false,
            alwayLinkToLastBuild: false,
            keepAll: true,
            reportDir: "logs",
            reportFiles: "index.html",
            reportName: "Build HTML Report"
        ])
    }
}


timestamps {
    timeout(time: 60, unit: "MINUTES") {
        parallel parallelSteps
    }
}
