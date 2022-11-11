echo "GO"
if [ "$is_test" = "true" ]
  then
    apt install -y cowsay
    echo "run tests"
    sleep 5
    python3.8 -m unittest -v -f /dedoc_root/tests/unit_tests/test* /dedoc_root/tests/api_tests/test_api*
    test_exit_code=$?
  if [ $test_exit_code -eq 0 ]
    then /usr/games/cowsay "all right"
    else /usr/games/cowsay -f dragon "tests failed"
  fi
  exit "$test_exit_code"
else
  echo "skip tests"
  echo "if you want to run tests do "
  echo 'tests="true" docker-compose up  --build --exit-code-from tests'
  echo 'if you want run only dedoc do'
  echo "docker-compose up --build dedoc"
fi
