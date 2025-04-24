document.addEventListener("DOMContentLoaded", () => {
    const puzzleDataElement = document.getElementById("puzzle-data");

    if (!puzzleDataElement) {
        return;
    }

    let piecesData;
    try {
        piecesData = JSON.parse(puzzleDataElement.textContent);
    } catch (error) {
        return;
    }

    if (!piecesData || piecesData.length === 0) {
        console.warn("No puzzle pieces found! Check if pieces are being sent from Django.");
    }

    // Matter.js setup
    const { Engine, Render, World, Bodies, Events, Runner, Body } = Matter;
    const engine = Engine.create();
    const world = engine.world;


    engine.world.gravity.y = 1.5;

    // Render setup
    const render = Render.create({
        element: document.body,
        engine: engine,
        canvas: document.getElementById("puzzleCanvas"),
        options: { width: 800, height: 600, wireframes: false, background: "#121212" }
    });


    let bar = Bodies.rectangle(400, 550, 250, 20, {
        isStatic: false, 
        friction: 0.1,
        restitution: 0.2,
        render: { fillStyle: "gray" }
    });
    World.add(world, bar);

    let outline = Bodies.rectangle(400, 500, 250, 150, {
        isStatic: false, // Make it dynamic
        friction: 0.1,
        restitution: 0.2,
        render: {
            fillStyle: "rgba(0, 255, 0, 0.2)",
            strokeStyle: "rgba(0, 255, 0, 0.5)",
            lineWidth: 2
        }
    });
    World.add(world, outline);

    const barOutlineConstraint = Matter.Constraint.create({
        bodyA: bar,
        bodyB: outline,
        pointB: { x: 0, y: -50 }, // Outline is 50 units above the bar
        stiffness: 1,
        length: 0
    });
    World.add(world, barOutlineConstraint);

    document.addEventListener("keydown", (event) => {
        if (event.key === "ArrowLeft") {
            Body.setVelocity(bar, { x: -5, y: 0 });
        } else if (event.key === "ArrowRight") {
            Body.setVelocity(bar, { x: 5, y: 0 });
        }
    });

    // Walls to keep pieces inside the area
    const walls = [
        Bodies.rectangle(400, 600, 800, 20, { isStatic: true }), // Ground
        Bodies.rectangle(0, 300, 20, 600, { isStatic: true }), // Left Wall
        Bodies.rectangle(800, 300, 20, 600, { isStatic: true }) // Right Wall
    ];
    World.add(world, walls);

    let pieceBodies = [];
    let currentPieceIndex = 0;

    function dropNextPiece() {
        if (currentPieceIndex >= piecesData.length) {
            return;
        }

        const piece = piecesData[currentPieceIndex];

        const puzzlePiece = Bodies.rectangle(
            400, -50, // Start at the top
            80, 80, // Size of the piece
            {
                restitution: 0.1,
                friction: 0.5,
                density: 0.005,
                render: {
                    sprite: {
                        texture: piece.image_url,
                        xScale: 0.5,
                        yScale: 0.5
                    }
                }
            }
        );

        puzzlePiece.correctX = piece.correct_x; // Correct X position
        puzzlePiece.correctY = piece.correct_y; // Correct Y position

        pieceBodies.push(puzzlePiece);
        World.add(world, puzzlePiece);

        currentPieceIndex++; // Move to the next piece
        setTimeout(dropNextPiece, 2000); // Drop next piece after 2 sec
    }

    Events.on(engine, "afterUpdate", () => {
        pieceBodies.forEach(piece => {
            // Check if the piece is inside the green outline
            if (
                piece.position.x > outline.position.x - 125 && // Left edge of outline
                piece.position.x < outline.position.x + 125 && // Right edge of outline
                piece.position.y > outline.position.y - 75 && // Top edge of outline
                piece.position.y < outline.position.y + 75 // Bottom edge of outline
            ) {
                Body.setPosition(piece, { x: piece.correctX, y: outline.position.y - 40 });
                Body.setStatic(piece, true); // Make the piece static (stop it from moving)
            }
        });
    });

    // 
    const runner = Runner.create();
    Runner.run(runner, engine);
    Render.run(render);

    //
    setTimeout(dropNextPiece, 1000);
});