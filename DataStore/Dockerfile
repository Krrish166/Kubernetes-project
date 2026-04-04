# stage-1
FROM amazoncorretto:11-alpine-jdk AS builder
WORKDIR /app/source
COPY . .
RUN ./mvnw clean package -Dspring.profiles.active=build -DskipTests

# stage-2
FROM amazoncorretto:11-alpine-jdk
COPY --from=builder /app/source/target/*.jar /app/app.jar
EXPOSE 8082
#RUN apk add --no-cache curl
#HEALTHCHECK --interval=20s --timeout=3s \
#  CMD curl -f http://localhost:8082/actuator/health || exit 1
CMD ["java", "-jar", "/app/app.jar"]