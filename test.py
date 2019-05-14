import asyncio
import requests
import functools

loginTask = None
logoutTask = None


async def perform_login(url):
    print("Commencing login... Gimme 2 seconds")
    await asyncio.sleep(2)
    response = requests.patch(url, json={'is_using': True})
    print(response.json())
    print("Login: Waiting for 10 seconds before allowing logout...")
    await asyncio.sleep(10)


async def perform_logout(url):
    print("Logout: Waiting for login to finish...")
    if loginTask:
        await loginTask
    print("Login finished! Commencing logout...")
    response = requests.patch(url, json={'is_using': False})
    print(response.json())


async def main():
    global loginTask, logoutTask
    loginTask = asyncio.create_task(
      perform_login('https://unlockitsocketapp.herokuapp.com/api/simple/students/798438730206/')
    )
    logoutTask = asyncio.create_task(
      perform_logout('https://unlockitsocketapp.herokuapp.com/api/simple/students/798438730206/')
    )
    # loginTask = asyncio.create_task(
    #     perform_login('http://127.0.0.1:8000/api/simple/students/456/')
    # )
    # logoutTask = asyncio.create_task(
    #     perform_logout('http://127.0.0.1:8000/api/simple/students/456/')
    # )

    await loginTask
    await logoutTask

asyncio.run(main())
