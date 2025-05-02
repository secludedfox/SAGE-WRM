// LCD Lines...
const lcd0 = document.getElementById("LCDLINE0");
const lcd1 = document.getElementById("LCDLINE1");
const lcd2 = document.getElementById("LCDLINE2");
const lcd3 = document.getElementById("LCDLINE3");


function send_button(event) {
	// console.log(`A button was pressed: ${event.target.id}`);

	fetch('/api/receive_button', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({"button": event.target.id})
	})
		.then(response => {
			if (!response.ok) {
				throw new Error(`HTTP error ${response.status}`);
			}
		})
		.catch(error => {
			console.error('Error sending POST:', error);
		});
}

function startPolling() {
	setInterval(async () => {
		try {
			const response = await fetch("/api/get_screen");
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}`);
			}
			const data = await response.json();
			UpdateDisplay(data);
		} catch (err) {
			console.error("Error:", err);
		}
	}, 500);
}

function UpdateDisplay(data) {
	lcd0.innerText = data[0];
	lcd1.innerText = data[1];
	lcd2.innerText = data[2];
	lcd3.innerText = data[3];
}

function main() {

	for (let i = 0; i < 4; i++) {
		const button = document.querySelector(`#bt${i}`);
		button.addEventListener("click", send_button);
	}

	document.addEventListener('DOMContentLoaded', startPolling);
}

main();
