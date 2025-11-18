#include <mcp_can.h>
#include <SPI.h>

#define FIRMWARE_VERSION "2.3"
// Define CS pin for MCP2515
const int SPI_CS_PIN = 9;
// Create an MCP_CAN object
MCP_CAN CAN0(SPI_CS_PIN); // Set CS pin

long unsigned int rxId; // To store the received message ID
unsigned char len = 0;   // To store the received message Data Length Code
unsigned char rxBuf[8];  // Buffer to store received data bytes

void setup() {
  // Initialise MCP2515 CAN controller, arguments: Speed (CAN_500KBPS), Crystal Frequency (MCP_16MHZ)
  if (CAN0.begin(MCP_ANY, CAN_500KBPS, MCP_16MHZ) == CAN_OK) {

  } else {
    Serial.println("Error Initialising MCP2515...");
    while (1); // Halt if initialisation fails
  }
  Serial.begin(115200);
  delay(100);
  while (!Serial); // Wait for serial port to connect
  Serial.print("##VER:");
  Serial.println(FIRMWARE_VERSION);
  Serial.println("##START"); // Tells python code to start timestamping
  // Set operation mode to normal to receive messages
  CAN0.setMode(MCP_NORMAL); 
}

void loop() {
  // Check if data is available
  if (CAN0.checkReceive() == CAN_MSGAVAIL) {
    // Read the data: ID, DLC, Data bytes
    CAN0.readMsgBuf(&rxId, &len, rxBuf);
    // Print the CAN ID
    Serial.print("0x");
    Serial.print(rxId, HEX);
    // Print the Data Length Code
    Serial.print("  dlc: ");
    Serial.print(len);
    Serial.print("  ");
    // Print the data payload
    for (int i = 0; i < len; i++) {
      if (rxBuf[i] < 0x10) { // Add leading zero for single hex digit
        Serial.print("0");
      }
      Serial.print(rxBuf[i], HEX);
      Serial.print(" ");
    }
    Serial.println();
  }
  // Small delay to prevent spamming the serial port if no messages are received
  delay(10); 
}