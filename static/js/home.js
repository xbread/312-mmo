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
let velocity = { x: 1, y: 0 };  // Start moving to the right
let moveDelay = 100; // milliseconds between moves (100ms = 10 moves per second)
let lastMoveTime = 0;
let food = {
    x: Math.floor(Math.random() * (canvas.width / blockSize)),
    y: Math.floor(Math.random() * (canvas.height / blockSize))
}
let score = 0;


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

    snake.unshift(head);

    // Check if snake eats the food
    if (head.x === food.x && head.y === food.y) {
        score += 1;   // Increment score
        spawnFood();
        updateUserListDisplay(); // <- NEW FUNCTION we'll make
    } else {
        snake.pop(); // Only pop tail if not eating
    }
}

function spawnFood() {
    food = {
        x: Math.floor(Math.random() * (canvas.width / blockSize)),
        y: Math.floor(Math.random() * (canvas.height / blockSize))
    };
}

function resetGame() {
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

// Game loop
function gameLoop(currentTime) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    drawBackground();
    if (currentTime - lastMoveTime > moveDelay) {
        updateSnake();  // Move only after delay
        lastMoveTime = currentTime;
    }
    drawFood();
    drawSnake();
    console.log();

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
        const socket = io({
            auth: { token: authToken }
        });

        socket.on('connect', () => {
            console.log('Connected to WebSocket server.');
        });
        
        socket.on('update_users', (data) => {
            updateUserList(data.users);
        });
        
        socket.on('disconnect', () => {
            console.log('Disconnected from WebSocket server.');
        });
    } else {
        console.error('No auth_token found! WebSocket connection not attempted.');
    }

    function updateUserList(users) {
        const userList = document.getElementById('user-list');
        userList.innerHTML = '';
        users.forEach(username => {
            const div = document.createElement('div');
            div.className = 'user';
            div.textContent = username;
            div.setAttribute('data-name', username.toLowerCase());
            userList.appendChild(div);
        });
    }

    function updateUserListDisplay() {
        const userList = document.getElementById('user-list');
        const users = Array.from(userList.children).map(child => child.dataset.name);
        updateUserList(users.map(name => name.charAt(0).toUpperCase() + name.slice(1)));
    }
});
