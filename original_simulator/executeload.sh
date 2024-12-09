#!/bin/bash
nohup /home/abacus/go_http/endpointsim --count=100 --domain=jupiter --secret='232b58f0-fe0f-4a20-9042-b2f0953f0ce5' --name='/home/abacus/go_http/knames.txt' --port=34781 &> osx_log34781.out &
sleep 10
nohup /home/abacus/go_http/endpointsim --count=100 --domain=jupiter1 --secret='ceeda1a2-11d1-4228-a5e6-fbad112e169b' --name='/home/abacus/go_http/knames1.txt' --port=34751 &> osx_log34751.out &
sleep 10
nohup /home/abacus/go_http/endpointsim --count=100 --domain=jupiter2 --secret='b4d8da68-7dbb-458b-90fe-69c40badeb5b' --name='/home/abacus/go_http/knames1a.txt' --port=34787 &> osx_log34787.out &
sleep 10
nohup /home/abacus/go_http/endpointsim --count=100 --domain=jupiter3 --secret='079e08a7-1539-4a4e-81e5-fa9352f1f25d' --name='/home/abacus/go_http/knames1b.txt' --port=34783 &> osx_log34783.out &
sleep 10
nohup /home/abacus/go_http/endpointsim --count=100 --domain=jupiter4 --secret='3e9e1ea0-436f-436b-8dd9-09823be20a31' --name='/home/abacus/go_http/knames1c.txt' --port=34773 &> osx_log34773.out &
sleep 10
nohup /home/abacus/go_http/endpointsim --count=100 --domain=jupiter5 --secret='2f71e88a-a003-4451-80c6-e8d3c2589728' --name='/home/abacus/go_http/knames2.txt' --port=34785 &> osx_log34785.out &
sleep 10
nohup /home/abacus/go_http/endpointsim --count=100 --domain=jupiter6 --secret='cd9681a3-2013-43ab-8ccb-defa44629c90' --name='/home/abacus/go_http/knames2a.txt' --port=34775 &> osx_log34775.out &
sleep 10
nohup /home/abacus/go_http/endpointsim --count=100 --domain=jupiter7 --secret='35dcb99b-11b7-4728-ad37-494ab16fe885' --name='/home/abacus/go_http/knames2b.txt' --port=34779 &> osx_log34779.out &
sleep 10
nohup /home/abacus/go_http/endpointsim --count=100 --domain=jupiter8 --secret='ed579975-46a3-4b2d-9dcb-a011e18fea6e' --name='/home/abacus/go_http/knames2c.txt' --port=34777 &> osx_log34777.out &
sleep 10
nohup /home/abacus/go_http/endpointsim --count=100 --domain=jupiter9 --secret='6fd19fc2-8fb3-445e-a243-cb15b3edcc7d' --name='/home/abacus/go_http/knames3.txt' --port=34761 &> osx_log34761.out &
sleep 10
sleep 20
