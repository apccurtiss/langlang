process.stdin.setEncoding('utf8');

// I just want to say - Node IO is stupid.
process.stdin.on('readable', () => {
    let input = '';
    let chunk;
    while ((chunk = process.stdin.read()) !== null) {
        input += chunk;
    }
    try {
        console.log(JSON.stringify(exports.{{ entrypoint }}(input), null, 2));
        process.exit(0);
    }
    catch(e) {
        console.error(e.message);
        process.exit(1);
    }
});