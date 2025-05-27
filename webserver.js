const http = require("http").createServer(handler);
const fs = require("fs");
const io = require("socket.io")(http);
const { exec } = require("child_process");
const path = require("path");

http.listen(8080);

function handler(req, res) {
  let filePath = path.join(__dirname, "public", req.url === "/" ? "index.html" : req.url);
  const extname = path.extname(filePath).toLowerCase();
  const mimeTypes = {
    ".html": "text/html",
    ".js": "text/javascript",
    ".css": "text/css",
    ".json": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpg",
    ".gif": "image/gif",
    ".ico": "image/x-icon",
  };
  const contentType = mimeTypes[extname] || "application/octet-stream";

  fs.readFile(filePath, function (err, data) {
    if (err) {
      res.writeHead(404, { "Content-Type": "text/html" });
      return res.end("404 Not Found");
    }
    res.writeHead(200, { "Content-Type": contentType });
    res.write(data);
    return res.end();
  });
}

// Global flag to control random movement loop
let randomMovementActive = false;

io.sockets.on("connection", function (socket) {
  socket.on("move_forward", function (data) {
    if (data === 1) {
      const scriptPath = path.join(__dirname, "scripts", "move_forward_until_obstacle.py");
      socket.emit("move_forward", 1);

      const process = exec(`python3 ${scriptPath}`);
      let output = "";

      process.stdout.on("data", (data) => {
        output += data.toString();
      });

      process.on("close", () => {
        try {
          const result = JSON.parse(output);
          socket.emit("move_forward", result);
        } catch (err) {
          console.error("Forward script output parse error:", output);
        }
        socket.emit("move_forward", 0);
      });
    } else {
      socket.emit("move_forward", 0);
    }
  });

  socket.on("move_backwards", function (data) {
    if (data === 1) {
      const backScript = path.join(__dirname, "scripts", "move_backwards_random_turn.py");
      const forwardScript = path.join(__dirname, "scripts", "move_forward_until_obstacle.py");

      // Notify client backward script started
      socket.emit("move_backwards", 1);

      // Run backward + random turn script
      const backProcess = exec(`python3 ${backScript}`);

      let backOutput = "";

      backProcess.stdout.on("data", (chunk) => {
        backOutput += chunk.toString();
      });

      backProcess.on("close", () => {
        // Notify client backward script ended
        socket.emit("move_backwards", 0);

        // Try to parse output from backward script and send to client
        try {
          const backResult = JSON.parse(backOutput);
          socket.emit("move_backwards", backResult);
        } catch (err) {
          console.error("Failed to parse backward script output:", backOutput);
        }

        // Now start forward movement script
        socket.emit("move_forward", 1); // Notify client forward script started

        const forwardProcess = exec(`python3 ${forwardScript}`);

        let forwardOutput = "";

        forwardProcess.stdout.on("data", (chunk) => {
          forwardOutput += chunk.toString();
        });

        forwardProcess.on("close", () => {
          try {
            const forwardResult = JSON.parse(forwardOutput);
            socket.emit("move_forward", forwardResult);
          } catch (err) {
            console.error("Failed to parse forward script output:", forwardOutput);
          }

          socket.emit("move_forward", 0); // Notify client forward script ended
        });
      });
    } else {
      socket.emit("move_backwards", 0);
    }
  });


  socket.on("random_movement", function (data) {
    if (data === 1) {
      randomMovementActive = true;
      socket.emit("random_movement", 1);
      startRandomLoop(socket);
    } else {
      randomMovementActive = false;
      socket.emit("random_movement", 0);
    }
  });
});

// Recursive function to loop backward → forward while active
function startRandomLoop(socket) {
  if (!randomMovementActive) return;

  const backScript = path.join(__dirname, "scripts", "move_backwards_random_turn.py");
  const forwardScript = path.join(__dirname, "scripts", "move_forward_until_obstacle.py");

  exec(`python3 ${backScript}`, (error, stdout, stderr) => {
    if (error) {
      console.error("Backwards error:", stderr);
      return;
    }

    try {
      const backResult = JSON.parse(stdout);
      socket.emit("move_backwards", backResult);
    } catch (err) {
      console.error("Backwards parse error:", stdout);
    }

    if (!randomMovementActive) return;

    exec(`python3 ${forwardScript}`, (error2, stdout2, stderr2) => {
      if (error2) {
        console.error("Forward error:", stderr2);
        return;
      }

      try {
        const forwardResult = JSON.parse(stdout2);
        socket.emit("move_forward", forwardResult);
      } catch (err) {
        console.error("Forward parse error:", stdout2);
      }

      if (randomMovementActive) {
        startRandomLoop(socket);
      }
    });
  });
}
