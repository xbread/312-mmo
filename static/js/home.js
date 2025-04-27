let socket = null;
let gameRunning = false;


document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById('game-board');
    const ctx = canvas.getContext('2d');
    
    // Match canvas drawing size to visual size
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    
    // Clear and draw background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

// Example: Draw a simple snake (start with 1 block)
const snake = [{ x: 5, y: 5 }];
const blockSize = 20;
const otherPlayers = {};  // username -> snake body

let velocity = { x: 1, y: 0 };  // Start moving to the right
let moveDelay = 100; // milliseconds between moves (100ms = 10 moves per second)
let lastMoveTime = 0;
let food = { x: 0, y: 0 };  // Default empty food until server sends real food
let score = 0;


function setTopMessage(text) {
    const topMessage = document.getElementById('top-message');
    if (topMessage) {
        topMessage.textContent = text;
    }
}

function drawBackground() {
    for (let y = 0; y < canvas.height; y += blockSize) {
        for (let x = 0; x < canvas.width; x += blockSize) {
            if ((x / blockSize + y / blockSize) % 2 === 0) {
                ctx.fillStyle = '#a8d080'; // Light green
            } else {
                ctx.fillStyle = '#98c070'; // Slightly darker green
            }
            ctx.fillRect(x, y, blockSize, blockSize);
        }
    }
}

function updateSnake() {
    const head = { 
        x: snake[0].x + velocity.x, 
        y: snake[0].y + velocity.y 
    };

    // Check wall collision
    if (
        head.x < 0 || 
        head.y < 0 || 
        head.x * blockSize >= canvas.width || 
        head.y * blockSize >= canvas.height
    ) {
        console.log("You hit the wall! Game over.");
        resetGame();
        return;
    }

    // Self collision
    for (let i = 0; i < snake.length; i++) {
        if (head.x === snake[i].x && head.y === snake[i].y) {
            console.log("You ran into yourself! Game over.");
            resetGame();
            return;
        }
    }

    // Other players collision
    for (const sid in otherPlayers) {
        const enemySnake = otherPlayers[sid];
        if (!enemySnake || enemySnake.length === 0) continue;

        for (let i = 0; i < enemySnake.length; i++) {
            const part = enemySnake[i];
            if (head.x === part.x && head.y === part.y) {
                if (i === 0) { 
                    // Head collision
                    if (snake.length > enemySnake.length) {
                        console.log("You defeated another player (longer snake)!");
                        // You win the collision, maybe you grow or do nothing
                    } else if (snake.length < enemySnake.length) {
                        console.log("You hit a bigger snake's head! You die.");
                        resetGame();
                        return;
                    } else {
                        console.log("Same size head collision. Both should die maybe?");
                        resetGame();
                        return;
                    }
                } else {
                    // Body collision
                    console.log("You hit someone's body! You die.");
                    resetGame();
                    return;
                }
            }
        }
    }

    if (socket && socket.connected) {
        socket.emit('player_update', {
            snake: snake, // your snake body [{x, y}, {x, y}, ...]
        });
    }

    snake.unshift(head);

    if (head.x === food.x && head.y === food.y) {
        score += 1;
        socket.emit('food_eaten'); // Tell server you ate food
    } else {
        snake.pop();
    }
}

function spawnFood() {
    food = {
        x: Math.floor(Math.random() * (canvas.width / blockSize)),
        y: Math.floor(Math.random() * (canvas.height / blockSize))
    };
}

function resetGame() {
    if (socket && socket.connected) {
        socket.emit('player_died');
    }
    snake.length = 1;                // Reset to length 1
    snake[0] = { x: 5, y: 5 };        // Reset position
    velocity.x = 1;                  // Move right by default
    velocity.y = 0;
}

function drawSnake() {
    ctx.fillStyle = 'green';
    snake.forEach(part => {
        ctx.fillRect(part.x * blockSize, part.y * blockSize, blockSize, blockSize);
    });
}

function drawFood() {
    ctx.fillStyle = 'red';
    ctx.fillRect(food.x * blockSize, food.y * blockSize, blockSize, blockSize);
}

function drawOtherPlayers(allSnakes) {
    ctx.fillStyle = 'blue'; // Set once
    for (const sid in allSnakes) {
        const snakeBody = allSnakes[sid];
        if (!snakeBody) continue;
        snakeBody.forEach(part => {
            ctx.fillRect(part.x * blockSize, part.y * blockSize, blockSize, blockSize);
        });
    }
}

function startGame() {
    gameRunning = true;  // Allow snake to move
    console.log("Game Started!");
}

// Game loop
function gameLoop(currentTime) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    drawBackground();
    if (gameRunning) {    
        if (currentTime - lastMoveTime > moveDelay) {
            updateSnake();  // Move only after delay
            lastMoveTime = currentTime;
        }
        drawFood();
        drawSnake();
        // Draw all other players
        // Object.values(otherPlayers).forEach(playerSnake => {
        //     ctx.fillStyle = 'blue'; // other players are blue for now
        //     playerSnake.forEach(part => {
        //         ctx.fillRect(part.x * blockSize, part.y * blockSize, blockSize, blockSize);
        //     });
        // });
        drawOtherPlayers(otherPlayers);
    }


    requestAnimationFrame(gameLoop);
}

document.addEventListener('keydown', function(event) {
    switch(event.key) {
        case 'ArrowUp':
            if (velocity.y === 0) { velocity.x = 0; velocity.y = -1; }
            break;
        case 'ArrowDown':
            if (velocity.y === 0) { velocity.x = 0; velocity.y = 1; }
            break;
        case 'ArrowLeft':
            if (velocity.x === 0) { velocity.x = -1; velocity.y = 0; }
            break;
        case 'ArrowRight':
            if (velocity.x === 0) { velocity.x = 1; velocity.y = 0; }
            break;
    }
});


gameLoop(performance.now());

    if (authToken) {
         socket = io({
            auth: { token: authToken }
        });

        socket.on('food_update', (newFood) => {
            console.log('Received food at:', newFood);
            food = newFood;
        });

        socket.on('update_players', (allSnakes) => {
            // Clear previous otherPlayers
            for (const id in otherPlayers) {
                delete otherPlayers[id];
            }
        
            // Only add other players (not yourself)
            for (const id in allSnakes) {
                if (id !== socket.id) {
                    otherPlayers[id] = allSnakes[id];
                }
            }
        });

        socket.on('game_over', (data) => {
            console.log("Game Over! Waiting for players to ready up again.");
            gameRunning = false;
        
            if (data && data.winner) {
                setTopMessage(`${data.winner} wins!!!`);
            } else {
                setTopMessage("Game Over!");
            }
        });

        socket.on('connect', () => {
            console.log('Connected to WebSocket server.');
        });
        
        socket.on('update_users', (data) => {
            console.log(data);
            updateUserList(data.users);
        });
        
        socket.on('disconnect', () => {
            console.log('Disconnected from WebSocket server.');
        });

        socket.on('start_countdown', (data) => {
            console.log(data)
            food = data.food;       
            console.log('Game starting with food at:', food);

            for (const id in otherPlayers) {
                delete otherPlayers[id];
            }
            
            // Reset your own snake
            if (data.starting_positions && socket.id in data.starting_positions) {
                const pos = data.starting_positions[socket.id];
                snake.length = 1;
                snake[0] = { x: pos.x, y: pos.y };
                console.log('Spawned at:', pos);
            }

            let countdown = 5;
            const countdownInterval = setInterval(() => {
                if (countdown > 0) {
                    console.log(`Game starting in ${countdown}...`);
                    setTopMessage(`Game starting in ${countdown}...`);
                    countdown--;
                } else {
                    clearInterval(countdownInterval);
                    console.log('Game Start!');
                    setTopMessage("Game Started!");
                    startGame(); // <- You'll control starting the snake now
                }
            }, 1000);
        });
    } else {
        console.error('No auth_token found! WebSocket connection not attempted.');
    }

    function updateUserList(users) {
        const userList = document.getElementById('user-list');
        userList.innerHTML = '';
    
        users.forEach(user => {
            console.log(user);
            const div = document.createElement('div');
            div.className = 'user';
            div.setAttribute('data-name', user.username.toLowerCase());
    
            // Username
            const usernameSpan = document.createElement('span');
            usernameSpan.textContent = user.username;
            div.appendChild(usernameSpan);
    
            // Ready button
            const readyButton = document.createElement('button');
            readyButton.textContent = 'Ready';
            readyButton.className = 'ready-button';
    
            if (user.ready) {
                readyButton.classList.add('ready');
                readyButton.disabled = true;
            } else {
                readyButton.addEventListener('click', () => {
                    socket.emit('ready_up');
                    readyButton.classList.add('ready');
                    readyButton.disabled = true;
                });
            }
    
            div.appendChild(readyButton);
            userList.appendChild(div);
        });
    }
    
    

    
    

    // function updateUserListDisplay() {
    //     const userList = document.getElementById('user-list');
    //     const users = Array.from(userList.children).map(child => child.dataset.name);
    //     updateUserList(users.map(name => name.charAt(0).toUpperCase() + name.slice(1)));
    // }
});
