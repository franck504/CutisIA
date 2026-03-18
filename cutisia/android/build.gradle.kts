allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
subprojects {
    project.evaluationDependsOn(":app")
}

subprojects {
    val fixNamespace = Action<Project> {
        if (extensions.findByName("android") != null) {
            val android = extensions.getByName("android")
            try {
                val getNamespace = android.javaClass.getMethod("getNamespace")
                val setNamespace = android.javaClass.getMethod("setNamespace", String::class.java)
                if (getNamespace.invoke(android) == null) {
                    val defaultNamespace = "com.cutisia.app.plugins.${name.replace("-", "_")}"
                    setNamespace.invoke(android, defaultNamespace)
                }

                // Patch for tflite_v2 specifically to remove the package attribute from manifest
                if (name == "tflite_v2") {
                    val manifestFile = file("src/main/AndroidManifest.xml")
                    if (manifestFile.exists()) {
                        val content = manifestFile.readText()
                        if (content.contains("package=\"sq.flutter.tflite\"")) {
                            manifestFile.writeText(content.replace("package=\"sq.flutter.tflite\"", ""))
                        }
                    }
                }
            } catch (e: Exception) {
            }
        }
    }
    if (state.executed) {
        fixNamespace.execute(this)
    } else {
        afterEvaluate { fixNamespace.execute(this) }
    }
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
