# Full stack with fastAPI
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="SmartPlayAI", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")

template_engines = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def form_get(request: Request):
    return template_engines.TemplateResponse("form.html", {"request": request})


@app.post("/submit/", response_class=HTMLResponse)
async def form_post(request: Request, item_name: str = Form(...), item_desc: str = Form(...)):
    # Process the form data (e.g., save to database, perform calculations, etc.)
    result = {
        "item_name": item_name,
        "item_desc": item_desc
    }
    return template_engines.TemplateResponse("result.html", {"request": request, "result": result})


# to run this file use: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
