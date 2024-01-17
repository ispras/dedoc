if [ "$is_test" = "true" ]
  then
    apt install -y cowsay
    echo "run tests"
    sleep 5
    python3 -m unittest -v -f /labeling_root/labeling/tests/test*
    test_exit_code=$?
  if [ $test_exit_code -eq 0 ]
    then /usr/games/cowsay "all right"
    else /usr/games/cowsay -f dragon "tests failed"
  fi
  exit "$test_exit_code"
else
  echo "skip tests, if you want to run tests do "
  echo 'test="true" docker-compose up  --build --exit-code-from test'
fi
