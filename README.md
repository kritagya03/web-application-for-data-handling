# Web Application for Data Handling

A Web application I built for Wärtsilä after first year as an ELSYS student. The application is meant to make it easy for people with no software skills
to get their data plotted in an effective and intuitive manner. The code was uploaded to a Raspberry Pi Model 4 and made to run instantly when given power, connected to Wärtsilä's Wi-Fi. 
This is so that anyone who wants to the the application can simply power the Rpi and go to

```sh
http://Rpi-IP-adress:80
```

An explanation of how to use the application and how the algorithm that tracks the spikes of the data in provided in each folder. An algorithm made to track the spikes of the data is implimented in
the web application, because people often wish to analyze the state-of-charge (SOC) of a battery when plotted, which is what the spike taracking does and graphically shows.
