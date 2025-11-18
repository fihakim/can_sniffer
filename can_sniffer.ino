#include <mcp_can.h>
#include <SPI.h>

#define FIRMWARE_VERSION "2.0"
// Define CS pin for MCP2515
const int SPI_CS_PIN = 9;
// Define INT pin for MCP2515
const int CAN_INT_PIN = 2; 

// Create an MCP_CAN object
MCP_CAN CAN0(SPI_CS_PIN); // Set CS pin

long unsigned int rxId; // To store the received message ID
unsigned char len = 0;   // To store the received message Data Length Code
unsigned char rxBuf[8];  // Buffer to store received data bytes

void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.print("##VER:");
  Serial.println(FIRMWARE_VERSION);
  while (!Serial); // Wait for serial port to connect
  Serial.println("CAN Bus Sniffer Initialising...");
  // Initialise MCP2515 CAN controller, arguments: Speed (CAN_500KBPS), Crystal Frequency (MCP_16MHZ)
  if (CAN0.begin(MCP_ANY, CAN_500KBPS, MCP_16MHZ) == CAN_OK) {
    Serial.println("MCP2515 Initialised Successfully!");
  } else {
    Serial.println("Error Initialising MCP2515...");
    while (1); // Halt if initialisation fails
  }

  // Set operation mode to normal to receive messages
  CAN0.setMode(MCP_NORMAL); 
  Serial.println("CAN Sniffer Ready. Waiting for messages...");
  Serial.println("-----------------------------");
}

void loop() {
  // Check if data is available
  if (CAN0.checkReceive() == CAN_MSGAVAIL) {
    // Read the data: ID, DLC, Data bytes
    CAN0.readMsgBuf(&rxId, &len, rxBuf);
    Serial.println("Received CAN message!");
    // Print the CAN ID
    Serial.print("ID: 0x");
    Serial.print(rxId, HEX);
    // Print the Data Length Code
    Serial.print("  DLC: ");
    Serial.println(len);
    // Print the data payload
    Serial.print("Data: ");
    for (int i = 0; i < len; i++) {
      if (rxBuf[i] < 0x10) { // Add leading zero for single hex digit
        Serial.print("0");
      }
      Serial.print(rxBuf[i], HEX);
      Serial.print(" ");
    }
    Serial.println();
    Serial.println("-----------------------------");
  }
  // Small delay to prevent spamming the serial port if no messages are received
  delay(10); 
}