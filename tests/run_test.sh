if [ "$is_test" = "true" ]
  then
    echo "run tests"
    sleep 10
    echo "GO"
    python3.5 -m unittest -v -f /tests/api_tests/test* /tests/test_* /tests/units/test*
else
  echo "skip tests"
  echo "if you want to run tests do "
  echo 'test="true" docker-compose up  --build --exit-code-from test'
  echo 'if you want run only dedoc do'
  echo "docker-compose up --build dedoc"
fi
