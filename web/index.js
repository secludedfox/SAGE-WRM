window.addEventListener("DOMContentLoaded", () => {
    fetch('config.json')
    .then(response => response.json())
    .then(data => {
      main(data);
    });

});


function main(jsonconfig) {
    const lcd0 = document.getElementById("0");
    const lcd1 = document.getElementById("1");
    const lcd2 = document.getElementById("2");
    const lcd3 = document.getElementById("3");

    var READY = false


    for (let i = 0; i < 4; i++) {
        const button = document.querySelector(`#bt${i}`);
        button.addEventListener('click', send_cmd);
    }

    var ws_ip = jsonconfig["websocket_ip"]
    var ws_port = jsonconfig["websocket_port"]

    const websocket = new WebSocket(`ws://${ws_ip}:${ws_port}`);
      

    function send_cmd(ev) {
        if(READY == true)
        {
            websocket.send(ev.target.id)
        }

    }

    websocket.onmessage = ({ data }) => {
        var data_json = JSON.parse(data);
        lcd0.innerText = data_json[0];
        lcd1.innerText = data_json[1];
        lcd2.innerText = data_json[2];
        lcd3.innerText = data_json[3];
    };

    websocket.onopen = ({ev}) => {
        READY = true;
    }
}