echo "GO"
if [ "$is_test" = "true" ]
  then
    apt install -y cowsay
    echo "run tests"
    sleep 5
    python3 /dedoc_root/tests/run_tests.py
    test_exit_code=$?
  if [ $test_exit_code -eq 0 ]
    then /usr/games/cowsay "all right"
    else /usr/games/cowsay -f dragon "tests failed"
  fi
  exit "$test_exit_code"
else
  echo "skip tests"
  echo "if you want to run tests do "
  echo 'test="true" docker-compose up  --build --exit-code-from test'
  echo 'if you want run only dedoc do'
  echo "docker-compose up --build dedoc"
fi
