# To build, run the following command from the top level project directory:
#
# docker build -t jbardet97/karnak-endpoints:<upstream-version>-api.<n> .
#
# Do NOT tag this image as osirixfoundation/karnak — that shadows the
# upstream image, which does not contain this fork's REST API endpoints,
# and makes digest pins in consuming repos silently wrong.

# Based on build image containing maven, jdk and git
FROM maven:3.9-eclipse-temurin-21-jammy AS builder
WORKDIR /app

# Build the Spring Boot application with layers
COPY pom.xml .
COPY src ./src
RUN mvn -B package -P production
WORKDIR /app/bin
RUN cp ../target/karnak*.jar application.jar
RUN java -Djarmode=layertools -jar application.jar extract

# Build the final deployment image
FROM eclipse-temurin:21-jdk-jammy
WORKDIR /app

COPY --from=builder /app/bin/dependencies/ ./
RUN true
COPY --from=builder /app/bin/spring-boot-loader/ ./
RUN true
COPY --from=builder /app/bin/snapshot-dependencies/ ./
RUN true
COPY --from=builder /app/bin/application/ ./
RUN true
COPY tools/docker-entrypoint.sh .

EXPOSE 8080
ENTRYPOINT ["/app/docker-entrypoint.sh"]
