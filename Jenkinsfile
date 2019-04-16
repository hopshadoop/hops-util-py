pipeline {
  agent {
    node {
      label 'platform_testing'
    }
  }

  stages {
    stage ('setup') {
      steps {
        // Creates the virtualenv before proceeding
        sh """
        if [ ! -d $WORKSPACE/../hops-util-py-env ];
        then
          virtualenv --python=/usr/bin/python $WORKSPACE/../hops-util-py-env    
        fi
	$WORKSPACE/../hops-util-py-env/bin/pip install twine sphinx sphinx-autobuild recommonmark sphinx_rtd_theme jupyter_sphinx_theme hops
        rm -rf dist/*
        """
      }
		}
    stage ('build') {
      steps {
        sh """
        source $WORKSPACE/../hops-util-py-env/bin/activate
        python ./setup.py sdist
        """
      }
    }
    stage ('build-doc') {
      steps {
        sh """
        source $WORKSPACE/../hops-util-py-env/bin/activate
        cd docs; sphinx-apidoc -f -o source/ ../hops ../hops/distribute/ ../hops/launcher.py ../hops/grid_search.py ../hops/differential_evolution.py ../hops/random_search.py ../hops/version.py ../hops/constants.py; make html; cd ..
        """
      }
    }
    stage ('update-it-notebook') {
      when { 
        branch 'master' 
      }
      steps {
        sh 'scp it_tests/integration_tests.ipynb snurran:/var/www/hops/hops-util-py_tests'
      }
    }
    stage ('deploy-bin') {
      when { 
        not { 
          branch 'master' 
        } 
      }
      environment {
        PYPI = credentials('977daeb0-e1c8-43a0-b35a-fc37bb9eee9b')
      }
      steps {
        sh """
        source $WORKSPACE/../hops-util-py-env/bin/activate
    	  twine upload -u $PYPI_USR -p $PYPI_PSW dist/*
        """
      }
    }
    stage ('deploy-doc') {
      when { 
        not { 
          branch 'master' 
        } 
      }
      steps {
        sh 'scp -r docs/_build/html/* jenkins@hops-py.logicalclocks.com:/var/www/hops-py'
      }
    }
  }
}
