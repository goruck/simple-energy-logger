/**
 * Publishes Shelly plug switch status periodically to a MQTT Broker.
 * Tested on Shelly Plug Plus US.
 * 
 * Copyright (c) Lindo St. Angel 2023.
 */

let CONFIG = {
    switchId: 0,
    interval: 8000, /* reporting interval in ms */
    MQTTPublishTopic: "/status/switch:",
  };
  
  let SHELLY_ID = undefined;
  
  Shelly.call("Mqtt.GetConfig", "", function (res, err_code, err_msg, ud) {
    SHELLY_ID = res["topic_prefix"];
  });
  
  let notifyTimer = Timer.set(CONFIG.interval, true, function () {
    Shelly.call(
      "Switch.GetStatus",
      {
        id: CONFIG.switchId,
      },
      function (res, err_code, err_msg, ud) {
        if (typeof SHELLY_ID === "undefined") {
          return;
        }
        if (typeof res !== "undefined" || res !== null) {
          MQTT.publish(
            SHELLY_ID + CONFIG.MQTTPublishTopic + JSON.stringify(CONFIG.switchId),
            JSON.stringify(res),
            0,
            false
          );
        }
      }
    );
  });