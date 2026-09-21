set_project("VideoWorkspace")
set_version("1.0.0")

local function python_executable()
    if is_host("windows") then
        local virtualenv_python = path.join(os.projectdir(), ".venv", "Scripts", "python.exe")
        if os.isfile(virtualenv_python) then
            return virtualenv_python
        end
    else
        local virtualenv_python = path.join(os.projectdir(), ".venv", "bin", "python")
        if os.isfile(virtualenv_python) then
            return virtualenv_python
        end
    end
    return "python"
end

target("extract-audio")
    set_kind("phony")
    on_run(function ()
        os.vrunv(python_executable(), {path.join(os.projectdir(), "scripts", "extract_audio.py")})
    end)

target("transcribe")
    set_kind("phony")
    on_run(function ()
        os.vrunv(python_executable(), {path.join(os.projectdir(), "scripts", "audio_to_txt.py")})
    end)

target("pipeline")
    set_default(true)
    set_kind("phony")
    on_run(function ()
        os.vrunv(python_executable(), {path.join(os.projectdir(), "scripts", "extract_audio.py")})
        os.vrunv(python_executable(), {path.join(os.projectdir(), "scripts", "audio_to_txt.py")})
    end)
    on_clean(function ()
        local project_directory = os.projectdir()
        cprint("${dim}清理项目目录：%s", project_directory)
        for _, directory_name in ipairs({"audios", "texts"}) do
            local output_directory = path.join(project_directory, directory_name)
            os.rm(output_directory)
            os.mkdir(output_directory)
        end
        os.rm(path.join(project_directory, "scripts", "__pycache__"))
        cprint("${green}已清理 audios、texts 和 Python 缓存；videos 目录未作任何修改。")
    end)
