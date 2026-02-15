from fastapi import FastAPI
from fastapi.params import Body
from pydantic import BaseModel
from typing import Optional
from random import randrange


app = FastAPI()


class Post(BaseModel):
    title: str
    content: str
    published: bool = True
    rating: Optional[int] = None


my_posts = [{"title": "test_title", "content": "test_content", "id": 0},]



@app.get("/welcome/")
async def get_message():
    return {"message": "Welcome to RTasker api!"}

@app.get("/posts")
async def get_posts():
    return my_posts

@app.get("/posts/{id}")
async def get_post(id:int):
    for post in my_posts:
        if post["id"] == id:
            return post
    return {"message": "no post found"}

@app.post("/posts")
async def create_post(post:Post):
    if post.published:
        post_dict = post.model_dump()
        post_dict["id"] = randrange(1, 1_000_000)
        my_posts.append(post_dict)
        print(post_dict)
        return {"message":"post created", "post": post_dict}
    return {"message": "post not created"}
#title str, content str
